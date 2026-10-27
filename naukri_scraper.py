import datetime
import logging
import re
import sys
import time
from datetime import date, timedelta
from typing import Optional

import pandas as pd
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("NaukriScraper")

JOBSPY_COLUMNS = [
    "id",
    "site",
    "job_url",
    "job_url_direct",
    "title",
    "company",
    "location",
    "date_posted",
    "job_type",
    "salary_source",
    "interval",
    "min_amount",
    "max_amount",
    "currency",
    "is_remote",
    "job_level",
    "job_function",
    "listing_type",
    "emails",
    "description",
    "company_industry",
    "company_url",
    "company_logo",
    "company_url_direct",
    "company_addresses",
    "company_num_employees",
    "company_revenue",
    "company_description",
    "skills",
    "experience_range",
    "company_rating",
    "company_reviews_count",
    "vacancy_count",
    "work_from_home_type",
]


def _slugify(text: str) -> str:
    """Convert text like 'Mumbai, Maharashtra' or 'Python Developer' to 'mumbai' or 'python-developer'."""
    text = text.split(",")[0].strip()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)


def _parse_salary(sal_str: Optional[str]):
    """Extract min_amount, max_amount, interval, currency from Naukri salary string."""
    if not sal_str or "Not disclosed" in sal_str or "Unspecified" in sal_str:
        return None, None, None, None

    lacs_match = re.search(r"([\d\.]+)\s*-\s*([\d\.]+)\s*Lac", sal_str, re.I)
    if lacs_match:
        try:
            low = float(lacs_match.group(1)) * 100_000
            high = float(lacs_match.group(2)) * 100_000
            return low, high, "yearly", "INR"
        except (ValueError, TypeError):
            pass

    return None, None, None, None


def _parse_relative_date(text: Optional[str]) -> str:
    """Converts '1 day ago', '3 days ago', 'Few hours ago' to YYYY-MM-DD."""
    today = date.today()
    if not text:
        return str(today)

    t_lower = text.lower().strip()
    if any(w in t_lower for w in ["just now", "few hours", "today", "0 day", "moment"]):
        return str(today)

    m_day = re.search(r"(\d+)\s*day", t_lower)
    if m_day:
        return str(today - timedelta(days=int(m_day.group(1))))

    m_week = re.search(r"(\d+)\s*week", t_lower)
    if m_week:
        return str(today - timedelta(days=int(m_week.group(1)) * 7))

    m_month = re.search(r"(\d+)\s*month", t_lower)
    if m_month:
        return str(today - timedelta(days=int(m_month.group(1)) * 30))

    if "30+" in t_lower:
        return str(today - timedelta(days=30))

    return str(today)


def _build_naukri_url(
    search_term: str,
    location: Optional[str],
    page: int = 1,
    hours_old: Optional[int] = None,
    experience: Optional[int] = None,
) -> str:
    term_slug = _slugify(search_term)
    loc_slug = _slugify(location) if location else None

    if loc_slug:
        base = f"https://www.naukri.com/{term_slug}-jobs-in-{loc_slug}"
    else:
        base = f"https://www.naukri.com/{term_slug}-jobs"

    if page > 1:
        base = f"{base}-{page}"

    query_params = ["sort=f"]  # Sort by Date (newest first)
    if hours_old:
        days = max(1, hours_old // 24)
        if days <= 1:
            job_age = 1
        elif days <= 3:
            job_age = 3
        elif days <= 7:
            job_age = 7
        elif days <= 15:
            job_age = 15
        else:
            job_age = 30
        query_params.append(f"jobAge={job_age}")

    if experience is not None:
        query_params.append(f"experience={experience}")

    return f"{base}?{'&'.join(query_params)}"


def scrape_naukri(
    search_term: str,
    location: Optional[str] = None,
    results_wanted: int = 20,
    hours_old: Optional[int] = 168,
    experience: Optional[int] = None,
    headless: bool = True,
    delay_per_page: float = 2.0,
) -> pd.DataFrame:
    """
    Scrapes jobs from Naukri.com using a headless Playwright Firefox browser.
    Applies the freshness filter (jobAge), experience filter (experience), and date sorting (sort=f).
    """
    records = []
    seen_ids = set()
    page_num = 1
    max_days = (hours_old // 24) if hours_old else None

    logger.info(
        f"Starting Naukri scrape for '{search_term}' in '{location or 'All India'}' "
        f"(wanted: {results_wanted}, max age: {max_days or 'unlimited'} days, exp: {experience if experience is not None else 'any'})"
    )

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
            viewport={"width": 1366, "height": 768},
            locale="en-US",
        )
        page = context.new_page()

        while len(records) < results_wanted and page_num <= 10:
            url = _build_naukri_url(
                search_term,
                location,
                page=page_num,
                hours_old=hours_old,
                experience=experience,
            )
            logger.info(f"Naukri: Loading page {page_num} -> {url}")

            try:
                res = page.goto(url, wait_until="domcontentloaded", timeout=25000)
                if res and res.status != 200:
                    logger.warning(f"Naukri returned status {res.status} on page {page_num}")
                    break

                page.wait_for_selector(".srp-jobtuple-wrapper, .cust-job-tuple", timeout=10000)
                time.sleep(delay_per_page)

                cards = page.query_selector_all(".srp-jobtuple-wrapper, .cust-job-tuple")
                if not cards:
                    logger.info("Naukri: No more job cards found on page.")
                    break

                logger.info(f"Naukri: Found {len(cards)} job cards on page {page_num}")

                for c in cards:
                    title_el = c.query_selector(".title")
                    comp_el = c.query_selector(".comp-name")
                    url_el = c.query_selector("a.title")
                    loc_el = c.query_selector(".loc-wrap .locWdth, .loc-wrap")
                    exp_el = c.query_selector(".exp-wrap .expwdth, .exp-wrap")
                    sal_el = c.query_selector(".sal-wrap .sal, .sal-wrap")
                    desc_el = c.query_selector(".job-desc")
                    tag_els = c.query_selector_all(".tag-li")
                    rating_el = c.query_selector(".rating .star, .rating")
                    post_day_el = c.query_selector(".job-post-day, span.job-post-day")

                    job_url = url_el.get_attribute("href") if url_el else None
                    if not job_url:
                        continue

                    # Extract ID from URL
                    id_match = re.search(r"-(\d{10,})", job_url)
                    job_id = f"nk-{id_match.group(1)}" if id_match else f"nk-{hash(job_url)}"

                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    # Extract & Parse Date Posted
                    post_day_text = post_day_el.inner_text().strip() if post_day_el else ""
                    date_posted = _parse_relative_date(post_day_text)

                    # Verify max_days filter
                    if max_days is not None and post_day_text:
                        p_lower = post_day_text.lower()
                        m_w = re.search(r"(\d+)\s*week", p_lower)
                        if m_w and int(m_w.group(1)) * 7 > max_days:
                            continue
                        m_d = re.search(r"(\d+)\s*day", p_lower)
                        if m_d and int(m_d.group(1)) > max_days:
                            continue
                        if "30+" in p_lower and max_days < 30:
                            continue

                    title = title_el.inner_text().strip() if title_el else "N/A"
                    company = comp_el.inner_text().strip() if comp_el else "N/A"
                    loc_str = loc_el.inner_text().strip() if loc_el else (location or "India")
                    exp_str = exp_el.inner_text().strip() if exp_el else None
                    sal_str = sal_el.inner_text().strip() if sal_el else None
                    desc_str = desc_el.inner_text().strip() if desc_el else None
                    skills_list = [t.inner_text().strip() for t in tag_els if t.inner_text().strip()]
                    rating_val = None
                    if rating_el:
                        try:
                            rating_val = float(rating_el.inner_text().strip())
                        except (ValueError, TypeError):
                            pass

                    min_amt, max_amt, interval, currency = _parse_salary(sal_str)

                    is_remote = any(
                        "remote" in (x or "").lower() or "hybrid" in (x or "").lower()
                        for x in [title, loc_str, desc_str]
                    )

                    record = {
                        "id": job_id,
                        "site": "naukri",
                        "job_url": job_url,
                        "job_url_direct": job_url,
                        "title": title,
                        "company": company,
                        "location": loc_str,
                        "date_posted": date_posted,
                        "job_type": "fulltime",
                        "salary_source": "direct_data" if (min_amt or max_amt) else None,
                        "interval": interval,
                        "min_amount": min_amt,
                        "max_amount": max_amt,
                        "currency": currency,
                        "is_remote": is_remote,
                        "job_level": None,
                        "job_function": None,
                        "listing_type": "organic",
                        "emails": None,
                        "description": desc_str,
                        "company_industry": None,
                        "company_url": None,
                        "company_logo": None,
                        "company_url_direct": None,
                        "company_addresses": None,
                        "company_num_employees": None,
                        "company_revenue": None,
                        "company_description": None,
                        "skills": ", ".join(skills_list) if skills_list else None,
                        "experience_range": exp_str,
                        "company_rating": rating_val,
                        "company_reviews_count": None,
                        "vacancy_count": None,
                        "work_from_home_type": "Hybrid" if "hybrid" in loc_str.lower() else ("Remote" if is_remote else None),
                    }
                    records.append(record)

                    if len(records) >= results_wanted:
                        break

            except Exception as err:
                logger.error(f"Error scraping Naukri on page {page_num}: {err}")
                break

            page_num += 1

        browser.close()

    df = pd.DataFrame(records, columns=JOBSPY_COLUMNS)
    logger.info(f"Finished Naukri scrape: collected {len(df)} jobs.")
    return df
