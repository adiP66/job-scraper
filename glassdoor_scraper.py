#!/usr/bin/env python3
"""
glassdoor_scraper.py — Dedicated Anti-Bot Playwright Firefox Scraper for Glassdoor
Bypasses Cloudflare Turnstile bot challenges by isolating sessions in clean browser contexts.
Outputs normalized 34-column DataFrame conforming to the unified schema.
"""

import datetime
import logging
import re
import sys
import urllib.parse
from datetime import date, timedelta
from typing import Optional

import pandas as pd
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, Exception):
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GlassdoorScraper")

JOBSPY_COLUMNS = [
    "id", "site", "job_url", "job_url_direct", "title", "company", "location",
    "date_posted", "job_type", "salary_source", "interval", "min_amount", "max_amount",
    "currency", "is_remote", "job_level", "job_function", "listing_type", "emails",
    "description", "company_industry", "company_url", "company_logo", "company_url_direct",
    "company_addresses", "company_num_employees", "company_revenue", "company_description",
    "skills", "experience_range", "company_rating", "company_reviews_count", "vacancy_count",
    "work_from_home_type",
]

# Standard Glassdoor location identifiers for target regions
LOCATION_MAP = {
    "mumbai": ("C", "2851180"),
    "navi mumbai": ("C", "2851180"),
    "thane": ("C", "2851180"),
    "pune": ("C", "2856202"),
    "india": ("N", "115"),
    "remote": ("N", "115"),
}


def _parse_relative_date(text: Optional[str]) -> str:
    """Converts '24h', '3d', '2w', '30d+' to ISO date YYYY-MM-DD."""
    today = date.today()
    if not text:
        return str(today)

    t = text.lower().strip()
    if any(w in t for w in ["just now", "few hours", "today", "24h", "0d", "1d", "yesterday", "moment"]):
        return str(today)

    m_day = re.search(r"(\d+)\s*d", t)
    if m_day:
        return str(today - timedelta(days=int(m_day.group(1))))

    m_week = re.search(r"(\d+)\s*w", t)
    if m_week:
        return str(today - timedelta(days=int(m_week.group(1)) * 7))

    m_month = re.search(r"(\d+)\s*m", t)
    if m_month:
        return str(today - timedelta(days=int(m_month.group(1)) * 30))

    if "30+" in t or "30d+" in t:
        return str(today - timedelta(days=30))

    return str(today)


def _parse_salary(sal_str: Optional[str]):
    """Extracts min_amount, max_amount, interval, currency from Glassdoor salary strings."""
    if not sal_str:
        return None, None, None, None

    currency = "INR" if "₹" in sal_str else "USD" if "$" in sal_str else None
    clean = sal_str.replace(",", "")

    # Hourly rates: e.g. ₹50.00 - ₹100.00 Per hour
    if "hour" in sal_str.lower():
        m_hr = re.findall(r"[\d\.]+", clean)
        if len(m_hr) >= 2:
            return float(m_hr[0]), float(m_hr[1]), "hourly", currency
        elif len(m_hr) == 1:
            return float(m_hr[0]), None, "hourly", currency

    # Yearly Lacs: e.g. ₹3L - ₹6L or 3.5L - 7L
    m_lacs = re.findall(r"([\d\.]+)\s*L", clean, re.I)
    if len(m_lacs) >= 2:
        return float(m_lacs[0]) * 100_000, float(m_lacs[1]) * 100_000, "yearly", currency
    elif len(m_lacs) == 1:
        return float(m_lacs[0]) * 100_000, None, "yearly", currency

    # Standard annual amounts: e.g. ₹300000 - ₹600000
    m_std = re.findall(r"(\d{5,})", clean)
    if len(m_std) >= 2:
        return float(m_std[0]), float(m_std[1]), "yearly", currency
    elif len(m_std) == 1:
        return float(m_std[0]), None, "yearly", currency

    return None, None, None, None


def _get_location_params(location: Optional[str]) -> tuple[str, str]:
    if not location:
        return "N", "115"
    loc_lower = location.lower().strip()
    for key, val in LOCATION_MAP.items():
        if key in loc_lower:
            return val
    return "N", "115"


def scrape_glassdoor(
    search_term: str,
    location: Optional[str] = "Mumbai",
    results_wanted: int = 30,
    hours_old: Optional[int] = 168,
    headless: bool = True,
) -> pd.DataFrame:
    """
    Scrapes jobs from Glassdoor using isolated headless Playwright Firefox sessions.
    Bypasses Cloudflare Turnstile blocks by avoiding cookie/session accumulation.
    """
    records = []
    seen_ids = set()
    max_days = (hours_old // 24) if hours_old else None
    loc_t, loc_id = _get_location_params(location)
    encoded_term = urllib.parse.quote_plus(search_term)

    logger.info(f"Starting Glassdoor scrape for '{search_term}' in '{location or 'India'}' (max age: {max_days or 'unlimited'} days)")

    page_num = 1
    with sync_playwright() as p:
        browser = p.firefox.launch(
            headless=headless,
            firefox_user_prefs={
                "dom.webdriver.enabled": False,
                "useAutomationExtension": False,
            },
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
            viewport={"width": 1366, "height": 768},
            locale="en-US",
        )
        page = context.new_page()

        while len(records) < results_wanted and page_num <= 3:
            p_arg = f"&p={page_num}" if page_num > 1 else ""
            url = f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={encoded_term}&locT={loc_t}&locId={loc_id}{p_arg}"
            logger.info(f"Glassdoor: Loading page {page_num} -> {url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(2500)

                # Dismiss any pop-up or modal dialog
                dialog = page.query_selector("dialog, [aria-modal='true']")
                if dialog:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)

                cards = page.query_selector_all("[data-test='jobListing']")
                if not cards:
                    logger.info(f"Glassdoor: No job cards found on page {page_num} (Title: '{page.title()}')")
                    break

                logger.info(f"Glassdoor: Found {len(cards)} cards on page {page_num}")

                for c in cards:
                    title_el = c.query_selector("[data-test='job-title']")
                    emp_el = c.query_selector("[class*='EmployerProfile'], [data-test='employer-name']")
                    loc_el = c.query_selector("[data-test='emp-location']")
                    sal_el = c.query_selector("[data-test='detailSalary']")
                    age_el = c.query_selector("[data-test='job-age']")
                    snippet_el = c.query_selector("[data-test='descSnippet']")
                    link_el = c.query_selector("a[data-test='job-title'], a[class*='jobTitle']")

                    title = title_el.inner_text().strip() if title_el else "N/A"
                    raw_emp = emp_el.inner_text().strip() if emp_el else "N/A"
                    company = re.sub(r"[\r\n].*", "", raw_emp).strip()
                    loc_str = loc_el.inner_text().strip() if loc_el else (location or "India")
                    sal_str = sal_el.inner_text().strip() if sal_el else None
                    age_str = age_el.inner_text().strip() if age_el else ""
                    snippet = snippet_el.inner_text().strip() if snippet_el else ""

                    job_url = link_el.get_attribute("href") if link_el else ""
                    if job_url and not job_url.startswith("http"):
                        job_url = f"https://www.glassdoor.co.in{job_url}"

                    if not job_url:
                        continue

                    id_match = re.search(r"jl=(\d+)", job_url)
                    job_id = f"gd-{id_match.group(1)}" if id_match else f"gd-{hash(job_url)}"

                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    # Freshness filter: Drop 30+ day old stale/sponsored postings
                    date_posted = _parse_relative_date(age_str)
                    if max_days is not None and age_str:
                        a_lower = age_str.lower()
                        if "30+" in a_lower or "30d+" in a_lower:
                            if max_days < 30:
                                continue
                        m_d = re.search(r"(\d+)\s*d", a_lower)
                        if m_d and int(m_d.group(1)) > max_days:
                            continue
                        m_w = re.search(r"(\d+)\s*w", a_lower)
                        if m_w and int(m_w.group(1)) * 7 > max_days:
                            continue

                    min_amt, max_amt, interval, currency = _parse_salary(sal_str)
                    is_remote = any(w in (x or "").lower() for x in [title, loc_str, snippet] for w in ["remote", "wfh", "work from home"])

                    record = {
                        "id": job_id,
                        "site": "glassdoor",
                        "job_url": job_url,
                        "job_url_direct": job_url,
                        "title": title,
                        "company": company,
                        "location": loc_str,
                        "date_posted": date_posted,
                        "job_type": "internship" if "intern" in title.lower() else "fulltime",
                        "salary_source": "direct_data" if (min_amt or max_amt) else None,
                        "interval": interval,
                        "min_amount": min_amt,
                        "max_amount": max_amt,
                        "currency": currency,
                        "is_remote": is_remote,
                        "job_level": "entry_level" if any(w in title.lower() for w in ["fresher", "intern", "junior", "trainee"]) else None,
                        "job_function": None,
                        "listing_type": "organic",
                        "emails": None,
                        "description": snippet,
                        "company_industry": None,
                        "company_url": None,
                        "company_logo": None,
                        "company_url_direct": None,
                        "company_addresses": None,
                        "company_num_employees": None,
                        "company_revenue": None,
                        "company_description": None,
                        "skills": None,
                        "experience_range": None,
                        "company_rating": None,
                        "company_reviews_count": None,
                        "vacancy_count": None,
                        "work_from_home_type": "Remote" if is_remote else None,
                    }
                    records.append(record)

                    if len(records) >= results_wanted:
                        break

            except Exception as err:
                logger.error(f"Error during Glassdoor scrape on page {page_num}: {err}")
                break

            page_num += 1

        browser.close()

    df = pd.DataFrame(records, columns=JOBSPY_COLUMNS)
    logger.info(f"Finished Glassdoor scrape: collected {len(df)} jobs for '{search_term}'.")
    return df


if __name__ == "__main__":
    df_test = scrape_glassdoor(search_term="python fresher", location="Mumbai", results_wanted=10, hours_old=360)
    print("\n--- Glassdoor Scrape Test Output ---")
    print(f"Total jobs collected: {len(df_test)}")
    if not df_test.empty:
        print(df_test[["title", "company", "location", "date_posted", "salary_source", "job_url"]].to_string())
