import csv
import datetime
import io
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
    folder = f"scrape_{timestamp}_last_3_days"
    os.makedirs(folder, exist_ok=True)
    today_str = str(datetime.date.today())

    print(f"=== Starting 3-Day Window Scrape (Last 72 Hours) into: {folder} ===")
    scraped_dfs = []

    # 1. JobSpy Streams (LinkedIn & Indeed) with hours_old=72
    print("\n--- 1. Scraping LinkedIn & Indeed (Strictly Last 72 Hours / 3 Days) ---")
    jobspy_configs = [
        {"term": "python fresher", "loc": "Mumbai, Maharashtra", "wanted": 30},
        {"term": "ai intern", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "ai intern", "loc": "India", "wanted": 30},
        {"term": "generative ai", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "generative ai", "loc": "India", "wanted": 25},
        {"term": "rag python", "loc": "India", "wanted": 25},
        {"term": "fastapi", "loc": "India", "wanted": 25},
        {"term": "langchain", "loc": "India", "wanted": 25},
        {"term": "machine learning fresher", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "ai engineer", "loc": "Pune, Maharashtra", "wanted": 25},
        {"term": "python developer", "loc": "Pune, Maharashtra", "wanted": 25},
        {"term": "junior ai engineer", "loc": "Mumbai, Maharashtra", "wanted": 25},
    ]

    for cfg in jobspy_configs:
        try:
            print(f"  JobSpy searching: '{cfg['term']}' in {cfg['loc']} (last 72h)...")
            df_q = scrape_jobs(
                site_name=["indeed", "linkedin"],
                search_term=cfg["term"],
                location=cfg["loc"],
                results_wanted=cfg["wanted"],
                hours_old=72,
                country_indeed="India",
                linkedin_fetch_description=True
            )
            print(f"  -> Got {len(df_q)} jobs for '{cfg['term']}' ({cfg['loc']})")
            if not df_q.empty:
                scraped_dfs.append(df_q)
        except Exception as e:
            print(f"  Error on '{cfg['term']}': {e}")

    # 2. Glassdoor Scrape (Last 3 Days)
    print("\n--- 2. Scraping Glassdoor (Last 3 Days) ---")
    gd_terms = ["python", "ai engineer", "data engineer", "fastapi"]
    for term in gd_terms:
        try:
            print(f"  Glassdoor searching: '{term}' in Mumbai...")
            df_gd = scrape_glassdoor(term, "Mumbai", results_wanted=20)
            print(f"  -> Got {len(df_gd)} jobs from Glassdoor for '{term}'")
            if not df_gd.empty:
                scraped_dfs.append(df_gd)
        except Exception as e:
            print(f"  Error on Glassdoor '{term}': {e}")

    # 3. Naukri Streams (Last 3 Days: jobAge=3)
    print("\n--- 3. Scraping Naukri (Strictly Last 3 Days / jobAge=3) ---")
    naukri_configs = [
        {"term": "python", "loc": "Mumbai", "wanted": 30, "age": 3, "exp": 0, "label": "Python (Exp: 0 Yrs, Mumbai)"},
        {"term": "ai engineer", "loc": "Mumbai", "wanted": 30, "age": 3, "exp": 0, "label": "AI Engineer (Exp: 0 Yrs, Mumbai)"},
        {"term": "generative ai", "loc": "Mumbai", "wanted": 25, "age": 3, "exp": None, "label": "Generative AI (Mumbai)"},
        {"term": "ai agent", "loc": "Mumbai", "wanted": 25, "age": 3, "exp": None, "label": "AI Agent (Mumbai)"},
        {"term": "langchain", "loc": "Mumbai", "wanted": 25, "age": 3, "exp": None, "label": "LangChain (Mumbai)"},
        {"term": "fastapi", "loc": "Mumbai", "wanted": 20, "age": 3, "exp": None, "label": "FastAPI (Mumbai)"},
        {"term": "python", "loc": "Pune", "wanted": 30, "age": 3, "exp": 0, "label": "Python (Exp: 0 Yrs, Pune)"},
        {"term": "ai engineer", "loc": "Pune", "wanted": 30, "age": 3, "exp": 0, "label": "AI Engineer (Exp: 0 Yrs, Pune)"},
        {"term": "machine learning", "loc": "Pune", "wanted": 25, "age": 3, "exp": 0, "label": "Machine Learning (Exp: 0 Yrs, Pune)"},
        {"term": "generative ai", "loc": "Pune", "wanted": 25, "age": 3, "exp": None, "label": "Generative AI (Pune)"},
        {"term": "python", "loc": "All India", "wanted": 30, "age": 3, "exp": 0, "label": "Python (Exp: 0 Yrs, Pan-India)"},
        {"term": "ai engineer", "loc": "All India", "wanted": 30, "age": 3, "exp": 0, "label": "AI Engineer (Exp: 0 Yrs, Pan-India)"},
    ]

    for cfg in naukri_configs:
        try:
            print(f"  Naukri scraping: {cfg['label']}...")
            df_n = scrape_naukri(
                search_term=cfg["term"],
                location=cfg["loc"],
                results_wanted=cfg["wanted"],
                hours_old=cfg["age"] * 24,
                experience=cfg["exp"]
            )
            print(f"  -> Got {len(df_n)} jobs for {cfg['label']}")
            if not df_n.empty:
                scraped_dfs.append(df_n)
        except Exception as e:
            print(f"  Error on Naukri '{cfg['label']}': {e}")

    if not scraped_dfs:
        print("No jobs scraped!")
        return

    all_jobs = pd.concat(scraped_dfs, ignore_index=True)
    before_dedup = len(all_jobs)
    all_jobs.drop_duplicates(subset=["job_url"], keep="first", inplace=True)
    all_jobs.drop_duplicates(subset=["title", "company"], keep="first", inplace=True)
    print(f"\nTotal raw jobs collected: {before_dedup} -> After dedup: {len(all_jobs)}")
    print("\nJob counts by site:")
    print(all_jobs["site"].value_counts())

    # Save raw jobs.csv
    jobs_csv_path = os.path.join(folder, "jobs.csv")
    all_jobs.to_csv(jobs_csv_path, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False, encoding="utf-8")
    print(f"\nSaved raw jobs to: {jobs_csv_path}")

    # 4. Deep Evaluation and Thorough De-duplication
    print("\n--- 4. Comprehensive Deduplication & Evaluation against Applied Registry ---")
    applied_tracker = load_applied_tracker()
    seen_tracker = load_seen_shortlist()
    today_str = datetime.date.today().isoformat()
    if applied_tracker:
        print(f"Loaded {len(applied_tracker['ids'])} already applied records.")
    if seen_tracker:
        print(f"Loaded {len(seen_tracker['ids'])} historical seen records.")

    shortlist_rows = []
    already_applied_list = []
    previously_shortlisted_list = []
    skip_count = 0
    already_applied_count = 0
    previously_shortlisted_count = 0

    for _, row in all_jobs.iterrows():
        tier, exp_label, why = evaluate_job(
            row,
            applied_tracker=applied_tracker,
            seen_tracker=seen_tracker,
            current_date=today_str
        )

        if exp_label == "Already Applied":
            already_applied_count += 1
            already_applied_list.append({
                "title": str(row.get("title") or ""),
                "company": str(row.get("company") or ""),
                "site": str(row.get("site") or ""),
                "date_posted": str(row.get("date_posted") or ""),
                "job_url": str(row.get("job_url") or ""),
                "why": why
            })
            skip_count += 1
            continue

        if exp_label == "Previously Shortlisted":
            previously_shortlisted_count += 1
            previously_shortlisted_list.append({
                "title": str(row.get("title") or ""),
                "company": str(row.get("company") or ""),
                "site": str(row.get("site") or ""),
                "date_posted": str(row.get("date_posted") or ""),
                "job_url": str(row.get("job_url") or ""),
                "why": why
            })
            skip_count += 1
            continue

        if tier in ["APPLY", "SHOT"]:
            cid = get_canonical_job_id_or_url(str(row.get("job_url") or ""))
            shortlist_rows.append({
                "tier": tier,
                "title": row.get("title"),
                "company": row.get("company"),
                "site": row.get("site"),
                "date_posted": row.get("date_posted"),
                "location": row.get("location"),
                "experience_required": exp_label,
                "salary": f"{row.get('min_amount')} - {row.get('max_amount')}" if pd.notna(row.get("min_amount")) else "Not Disclosed",
                "job_url": row.get("job_url"),
                "why": why,
                "status": "Shortlisted",
                "applied_date": "",
                "canonical_id": cid
            })
        else:
            skip_count += 1

    shortlist_df = pd.DataFrame(shortlist_rows)

    # Secondary deduplication by company and title inside shortlist
    if not shortlist_df.empty:
        shortlist_df.drop_duplicates(subset=["company", "title"], keep="first", inplace=True)
        # Sort so APPLY tier comes first, then by date_posted descending
        shortlist_df.sort_values(by=["tier", "date_posted"], ascending=[True, False], inplace=True)

    shortlist_csv_path = os.path.join(folder, "apply_shortlist.csv")
    shortlist_df.to_csv(shortlist_csv_path, index=False, encoding="utf-8")
    print(f"Saved shortlisted jobs to: {shortlist_csv_path}")

    apply_count = len(shortlist_df[shortlist_df["tier"] == "APPLY"]) if not shortlist_df.empty else 0
    shot_count = len(shortlist_df[shortlist_df["tier"] == "SHOT"]) if not shortlist_df.empty else 0
    print(f"Total Shortlisted (NEW IN 3-DAY WINDOW): {len(shortlist_df)} (APPLY: {apply_count}, SHOT: {shot_count})")
    print(f"Total Filtered Out: {skip_count} ({already_applied_count} applied, {previously_shortlisted_count} previously shortlisted, {skip_count - already_applied_count - previously_shortlisted_count} non-match/stale/senior)")

    # Update seen registry with canonical IDs
    if not shortlist_df.empty:
        update_seen_shortlist(shortlist_df.to_dict(orient="records"), today_str)

    # 5. Generate Markdown Report
    report_path = os.path.join(folder, "job_fit_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 3-Day Window Fresher & Early-Career Job Fit Report (Last 72 Hours)\n\n")
        f.write(f"**Generated:** {datetime.date.today().strftime('%B %d, %Y')}\n\n")
        f.write("**Candidate:** Aditya Parkhe | MSc. AI (2026), BSc. CS (2024)\n")
        f.write("**Core Stack:** Python, FastAPI, RAG (LangChain/LangGraph/Chroma), Deep Learning/ML, AWS, PostgreSQL\n")
        f.write("**Time Window:** Strictly Last 72 Hours (October 2 – October 5, 2026)\n\n")
        f.write("---\n\n")
        f.write("## 1. Scraping & Pipeline Breakdown\n\n")
        f.write(f"| Metric | Count |\n|---|---|\n")
        f.write(f"| Total Raw Scraped | {len(all_jobs)} |\n")
        f.write(f"| Already Applied (De-duplicated) | {already_applied_count} |\n")
        f.write(f"| Previously Shortlisted (Cross-Day De-duplicated) | {previously_shortlisted_count} |\n")
        f.write(f"| Filtered Out (Senior/High Exp/Non-tech) | {skip_count - already_applied_count - previously_shortlisted_count} |\n")
        f.write(f"| **Total Verified Shortlisted (NEW IN 3-DAY WINDOW)** | **{len(shortlist_df)}** |\n")
        f.write(f"| — **Priority `APPLY` (0–1 Yr / Fresher / Junior)** | **{apply_count}** |\n")
        f.write(f"| — Reach `SHOT` (~2 Yrs / Portfolio Bridge) | {shot_count} |\n\n")

        f.write("### Platform Distribution\n\n")
        for site, cnt in all_jobs['site'].value_counts().items():
            f.write(f"- **{str(site).capitalize()}:** {cnt} jobs\n")
        f.write("\n---\n\n")

        f.write("## 2. Priority Applications (`APPLY` Tier — 0 to 1 Year / Fresher / Junior Only)\n\n")
        if apply_count > 0:
            for _, r in shortlist_df[shortlist_df["tier"] == "APPLY"].iterrows():
                f.write(f"### {r['title']} — {r['company']}\n")
                f.write(f"- **Source:** {str(r['site']).capitalize()} | **Posted:** {r['date_posted']} | **Location:** {r['location']}\n")
                f.write(f"- **Experience Required:** `{r['experience_required']}` | **Salary:** {r['salary']}\n")
                f.write(f"- **Job Link:** [{r['title']}]({r['job_url']})\n")
                f.write(f"- **Why Apply:** {r['why']}\n\n")
        else:
            f.write("No unapplied priority roles found in this window.\n\n")

        f.write("---\n\n")
        f.write("## 3. Stretch Opportunities (`SHOT` Tier — ~2 Years / Portfolio Bridge)\n\n")
        if shot_count > 0:
            for _, r in shortlist_df[shortlist_df["tier"] == "SHOT"].iterrows():
                f.write(f"### {r['title']} — {r['company']}\n")
                f.write(f"- **Source:** {str(r['site']).capitalize()} | **Posted:** {r['date_posted']} | **Location:** {r['location']}\n")
                f.write(f"- **Experience Required:** `{r['experience_required']}` | **Salary:** {r['salary']}\n")
                f.write(f"- **Job Link:** [{r['title']}]({r['job_url']})\n")
                f.write(f"- **Why & Strategy:** {r['why']}\n\n")
        else:
            f.write("No unapplied stretch opportunities found in this window.\n\n")

    print(f"\nGenerated report: {report_path}")
    print(f"All files saved in: {folder}/")

if __name__ == "__main__":
    main()
