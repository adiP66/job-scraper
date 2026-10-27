import csv
import datetime
import os
import re
import sys
import pandas as pd
from jobspy import scrape_jobs
from naukri_scraper import scrape_naukri
from glassdoor_scraper import scrape_glassdoor
from run_scrape_and_fit import (
    load_applied_tracker,
    load_seen_shortlist,
    update_seen_shortlist,
    evaluate_job,
    get_canonical_job_id_or_url
)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = f"scrape_{timestamp}_fresher_deep"
    os.makedirs(folder, exist_ok=True)
    today_str = str(datetime.date.today())

    print(f"=== Starting Targeted Fresher/Junior Deep Scrape into: {folder} ===")
    scraped_dfs = []

    # 1. JobSpy Streams (LinkedIn & Indeed) - Pure Fresher & Junior
    print("\n--- 1. Scraping LinkedIn & Indeed (Pure Early-Career / Intern / Junior) ---")
    jobspy_configs = [
        {"term": "junior ai engineer", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "junior ai engineer", "loc": "India", "wanted": 25},
        {"term": "ai intern", "loc": "India", "wanted": 25},
        {"term": "fresher python developer", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "entry level machine learning", "loc": "India", "wanted": 25},
        {"term": "rag python", "loc": "India", "wanted": 25},
        {"term": "langchain intern", "loc": "India", "wanted": 20},
        {"term": "generative ai fresher", "loc": "India", "wanted": 20},
    ]

    for cfg in jobspy_configs:
        try:
            print(f"  JobSpy searching: '{cfg['term']}' in {cfg['loc']}...")
            df_q = scrape_jobs(
                site_name=["indeed", "linkedin"],
                search_term=cfg["term"],
                location=cfg["loc"],
                results_wanted=cfg["wanted"],
                hours_old=168,
                country_indeed="India",
                linkedin_fetch_description=True
            )
            print(f"  -> Got {len(df_q)} jobs for '{cfg['term']}' ({cfg['loc']})")
            if not df_q.empty:
                scraped_dfs.append(df_q)
                # Incremental save
                interim_df = pd.concat(scraped_dfs, ignore_index=True).drop_duplicates(subset=["job_url"], keep="first")
                interim_df.to_csv(os.path.join(folder, "jobs.csv"), index=False)
        except Exception as e:
            print(f"  Error scraping JobSpy for '{cfg['term']}': {e}")

    # 2. Glassdoor Targeted Fresher Streams
    print("\n--- 2. Scraping Glassdoor (Early-Career / Intern Streams) ---")
    glassdoor_configs = [
        {"term": "ai intern", "loc": "Mumbai", "wanted": 20},
        {"term": "machine learning intern", "loc": "Mumbai", "wanted": 20},
        {"term": "junior ai engineer", "loc": "Mumbai", "wanted": 20},
        {"term": "python intern", "loc": "Mumbai", "wanted": 20},
    ]

    for cfg in glassdoor_configs:
        try:
            print(f"  Glassdoor scraping: '{cfg['term']}' in {cfg['loc']}...")
            df_gd = scrape_glassdoor(
                search_term=cfg["term"],
                location=cfg["loc"],
                results_wanted=cfg["wanted"],
                hours_old=168,
            )
            print(f"  -> Got {len(df_gd)} jobs from Glassdoor for '{cfg['term']}'")
            if not df_gd.empty:
                scraped_dfs.append(df_gd)
                interim_df = pd.concat(scraped_dfs, ignore_index=True).drop_duplicates(subset=["job_url"], keep="first")
                interim_df.to_csv(os.path.join(folder, "jobs.csv"), index=False)
        except Exception as e:
            print(f"  Error scraping Glassdoor for '{cfg['term']}': {e}")

    # 3. Naukri Pure 0-Exp Streams
    print("\n--- 3. Scraping Naukri (Strict 0 Yrs Experience Streams) ---")
    naukri_configs = [
        {"search_term": "ai engineer", "location": "Mumbai", "experience": 0, "wanted": 25, "label": "AI Engineer (Exp: 0, Mumbai)"},
        {"search_term": "machine learning", "location": "Mumbai", "experience": 0, "wanted": 25, "label": "Machine Learning (Exp: 0, Mumbai)"},
        {"search_term": "generative ai", "location": "Mumbai", "experience": 0, "wanted": 25, "label": "GenAI (Exp: 0, Mumbai)"},
        {"search_term": "python intern", "location": "Mumbai", "experience": None, "wanted": 25, "label": "Python Intern (Mumbai)"},
        {"search_term": "ai intern", "location": "Mumbai", "experience": None, "wanted": 25, "label": "AI Intern (Mumbai)"},
        {"search_term": "fastapi", "location": None, "experience": 0, "wanted": 20, "label": "FastAPI (Exp: 0, Pan-India)"},
        {"search_term": "langchain", "location": None, "experience": 0, "wanted": 20, "label": "LangChain (Exp: 0, Pan-India)"},
    ]

    for cfg in naukri_configs:
        try:
            print(f"  Naukri scraping: {cfg['label']}...")
            df_nk = scrape_naukri(
                search_term=cfg["search_term"],
                location=cfg.get("location"),
                results_wanted=cfg["wanted"],
                hours_old=168,
                experience=cfg.get("experience"),
                headless=True
            )
            print(f"  -> Got {len(df_nk)} jobs from Naukri for '{cfg['label']}'")
            if not df_nk.empty:
                scraped_dfs.append(df_nk)
                interim_df = pd.concat(scraped_dfs, ignore_index=True).drop_duplicates(subset=["job_url"], keep="first")
                interim_df.to_csv(os.path.join(folder, "jobs.csv"), index=False)
        except Exception as e:
            print(f"  Error scraping Naukri for '{cfg['label']}': {e}")

    if not scraped_dfs:
        print("No jobs scraped.")
        return

    all_jobs = pd.concat(scraped_dfs, ignore_index=True)
    all_jobs.drop_duplicates(subset=["job_url"], keep="first", inplace=True)
    print(f"\nTotal raw jobs collected: {len(all_jobs)}")
    print(all_jobs["site"].value_counts())

    raw_jobs_path = os.path.join(folder, "jobs.csv")
    all_jobs.to_csv(raw_jobs_path, index=False)

    applied_tracker = load_applied_tracker()
    seen_tracker = load_seen_shortlist()

    shortlist_rows = []
    already_applied_count = 0
    previously_shortlisted_count = 0
    skip_count = 0

    for _, row in all_jobs.iterrows():
        tier, exp_label, why = evaluate_job(row, applied_tracker=applied_tracker, seen_tracker=seen_tracker, current_date=today_str)
        if tier == "SKIP":
            skip_count += 1
            if exp_label == "Already Applied":
                already_applied_count += 1
            elif exp_label == "Previously Shortlisted":
                previously_shortlisted_count += 1
        elif tier in ["APPLY", "SHOT"]:
            comp = str(row.get("company") or "").lower()
            if "weintern" in comp or "bytepadna" in comp:
                continue
            min_sal = row.get("min_amount")
            max_sal = row.get("max_amount")
            salary_str = ""
            if pd.notna(min_sal) and pd.notna(max_sal):
                salary_str = f"₹{int(min_sal):,} - ₹{int(max_sal):,}"
            elif pd.notna(min_sal):
                salary_str = f"From ₹{int(min_sal):,}"

            shortlist_rows.append({
                "tier": tier,
                "title": str(row.get("title") or ""),
                "company": str(row.get("company") or ""),
                "site": str(row.get("site") or ""),
                "date_posted": str(row.get("date_posted") or ""),
                "location": str(row.get("location") or ""),
                "experience_required": exp_label,
                "salary": salary_str,
                "job_url": str(row.get("job_url") or ""),
                "why": why,
                "status": "Shortlisted",
                "applied_date": ""
            })

    df_shortlist = pd.DataFrame(shortlist_rows)
    if not df_shortlist.empty:
        df_shortlist.sort_values(by=["tier", "date_posted"], ascending=[True, False], inplace=True)

    shortlist_csv_path = os.path.join(folder, "apply_shortlist.csv")
    df_shortlist.to_csv(shortlist_csv_path, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False, encoding="utf-8")
    print(f"Saved shortlisted jobs to: {shortlist_csv_path}")

    apply_count = len(df_shortlist[df_shortlist['tier']=='APPLY']) if not df_shortlist.empty else 0
    shot_count = len(df_shortlist[df_shortlist['tier']=='SHOT']) if not df_shortlist.empty else 0
    print(f"Total Shortlisted (NEW TODAY): {len(df_shortlist)} (APPLY: {apply_count}, SHOT: {shot_count})")
    filtered_other = skip_count - already_applied_count - previously_shortlisted_count
    print(f"Total Filtered Out: {skip_count} ({already_applied_count} applied, {previously_shortlisted_count} previously shortlisted, {filtered_other} non-match/stale/senior)")

    if shortlist_rows:
        update_seen_shortlist(shortlist_rows, current_date=today_str)

    report_path = os.path.join(folder, "job_fit_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Targeted Pure Fresher / Early-Career Deep Scrape Report\n\n")
        f.write(f"**Generated:** {datetime.date.today().strftime('%B %d, %Y')}\n\n")
        f.write(f"**Candidate:** Aditya Parkhe | MSc. AI (2026), BSc. CS (2024)\n")
        f.write(f"**Focus:** 0-1 Yr Experience, Junior / Intern Roles Only\n\n")
        f.write(f"| Metric | Count |\n|---|---|\n")
        f.write(f"| Total Raw Scraped | {len(all_jobs)} |\n")
        f.write(f"| Already Applied | {already_applied_count} |\n")
        f.write(f"| Previously Shortlisted | {previously_shortlisted_count} |\n")
        f.write(f"| Filtered Out | {filtered_other} |\n")
        f.write(f"| **Verified Shortlisted** | **{len(df_shortlist)}** |\n\n")

        apply_jobs = df_shortlist[df_shortlist["tier"] == "APPLY"] if not df_shortlist.empty else pd.DataFrame()
        f.write("## 1. Priority Applications (`APPLY` Tier — 0 to 1 Year / Fresher / Junior Only)\n\n")
        for _, j in apply_jobs.iterrows():
            f.write(f"### {j['title']} — {j['company']}\n")
            f.write(f"- **Source:** {str(j['site']).capitalize()} | **Location:** {j['location']}\n")
            f.write(f"- **Experience:** {j['experience_required']}\n")
            f.write(f"- **Fit Reason:** {j['why']}\n")
            f.write(f"- **URL:** [Apply Here]({j['job_url']})\n\n")

    print(f"Report generated: {report_path}")

if __name__ == "__main__":
    main()
