import os
import datetime
import pandas as pd
from naukri_scraper import scrape_naukri
from run_scrape_and_fit import (
    load_applied_tracker,
    load_seen_shortlist,
    update_seen_shortlist,
    evaluate_job,
    get_canonical_job_id_or_url
)

def run_naukri_3_days():
    folder = "scrape_20261005_100615_last_3_days"
    print(f"=== Scraping Naukri for Last 3 Days into {folder} ===")
    
    naukri_configs = [
        {"term": "fastapi", "loc": "Mumbai", "wanted": 25, "exp": None, "label": "FastAPI (Mumbai)"},
        {"term": "fastapi", "loc": "All India", "wanted": 25, "exp": None, "label": "FastAPI (India)"},
        {"term": "langchain", "loc": "Mumbai", "wanted": 25, "exp": None, "label": "LangChain (Mumbai)"},
        {"term": "langchain", "loc": "All India", "wanted": 25, "exp": None, "label": "LangChain (India)"},
        {"term": "generative ai", "loc": "Mumbai", "wanted": 25, "exp": 0, "label": "GenAI Exp:0 (Mumbai)"},
        {"term": "generative ai", "loc": "All India", "wanted": 25, "exp": 0, "label": "GenAI Exp:0 (India)"},
        {"term": "ai engineer", "loc": "Mumbai", "wanted": 25, "exp": 0, "label": "AI Eng Exp:0 (Mumbai)"},
        {"term": "ai engineer", "loc": "Pune", "wanted": 25, "exp": 0, "label": "AI Eng Exp:0 (Pune)"},
        {"term": "python developer", "loc": "Mumbai", "wanted": 25, "exp": 0, "label": "Python Exp:0 (Mumbai)"},
        {"term": "python developer", "loc": "Pune", "wanted": 25, "exp": 0, "label": "Python Exp:0 (Pune)"},
    ]

    scraped = []
    for cfg in naukri_configs:
        try:
            print(f"  Scraping Naukri: {cfg['label']}...")
            df = scrape_naukri(
                search_term=cfg["term"],
                location=cfg["loc"],
                results_wanted=cfg["wanted"],
                hours_old=72,
                experience=cfg["exp"]
            )
            print(f"  -> Got {len(df)} jobs for {cfg['label']}")
            if not df.empty:
                scraped.append(df)
        except Exception as e:
            print(f"  Error on {cfg['label']}: {e}")

    if not scraped:
        print("No new jobs scraped from Naukri.")
        return

    naukri_all = pd.concat(scraped, ignore_index=True)
    naukri_all.drop_duplicates(subset=["job_url"], keep="first", inplace=True)
    naukri_all.drop_duplicates(subset=["title", "company"], keep="first", inplace=True)
    print(f"\nTotal unique Naukri jobs scraped: {len(naukri_all)}")

    # Merge with existing jobs.csv
    jobs_csv_path = os.path.join(folder, "jobs.csv")
    if os.path.exists(jobs_csv_path):
        existing_jobs = pd.read_csv(jobs_csv_path, encoding="utf-8")
        merged_jobs = pd.concat([existing_jobs, naukri_all], ignore_index=True)
        merged_jobs.drop_duplicates(subset=["job_url"], keep="first", inplace=True)
        merged_jobs.drop_duplicates(subset=["title", "company"], keep="first", inplace=True)
    else:
        merged_jobs = naukri_all

    merged_jobs.to_csv(jobs_csv_path, index=False, encoding="utf-8")
    print(f"Updated raw jobs pool in {jobs_csv_path}: {len(merged_jobs)} total unique jobs.")

    # Re-evaluate all jobs against applied tracker and seen shortlist
    applied_tracker = load_applied_tracker()
    seen_tracker = load_seen_shortlist()

    shortlist_rows = []
    skip_count = 0
    already_applied_count = 0
    previously_shortlisted_count = 0

    for _, row in merged_jobs.iterrows():
        tier, exp_label, why = evaluate_job(row, applied_tracker, seen_tracker)
        if tier in ("APPLY", "SHOT"):
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
            if "Already applied" in why:
                already_applied_count += 1
            elif "Previously shortlisted" in why:
                previously_shortlisted_count += 1

    shortlist_df = pd.DataFrame(shortlist_rows)
    if not shortlist_df.empty:
        shortlist_df.drop_duplicates(subset=["company", "title"], keep="first", inplace=True)
        shortlist_df.sort_values(by=["tier", "date_posted"], ascending=[True, False], inplace=True)

    shortlist_csv_path = os.path.join(folder, "apply_shortlist.csv")
    shortlist_df.to_csv(shortlist_csv_path, index=False, encoding="utf-8")
    print(f"Saved shortlisted jobs to: {shortlist_csv_path}")

    today_str = str(datetime.date.today())
    if not shortlist_df.empty:
        update_seen_shortlist(shortlist_df.to_dict(orient="records"), today_str)

    apply_count = len(shortlist_df[shortlist_df["tier"] == "APPLY"]) if not shortlist_df.empty else 0
    shot_count = len(shortlist_df[shortlist_df["tier"] == "SHOT"]) if not shortlist_df.empty else 0
    print(f"Total Shortlisted (NEW IN 3-DAY WINDOW): {len(shortlist_df)} (APPLY: {apply_count}, SHOT: {shot_count})")

    # Generate Markdown Report
    report_path = os.path.join(folder, "job_fit_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 3-Day Window Fresher & Early-Career Job Fit Report (Last 72 Hours)\n\n")
        f.write(f"**Generated:** {datetime.date.today().strftime('%B %d, %Y')}\n\n")
        f.write("**Candidate:** Aditya Parkhe | MSc. AI (2026), BSc. CS (2024)\n")
        f.write("**Core Stack:** Python, FastAPI, RAG (LangChain/LangGraph/Chroma), Deep Learning/ML, AWS, PostgreSQL\n")
        f.write("**Time Window:** Strictly Last 72 Hours (October 2 – October 5, 2026)\n\n")
        f.write("---\n\n")
        f.write("## 1. Scraping & Pipeline Breakdown\n\n")
        f.write("| Metric | Count |\n|---|---|\n")
        f.write(f"| Total Raw Scraped | {len(merged_jobs)} |\n")
        f.write(f"| Already Applied (De-duplicated) | {already_applied_count} |\n")
        f.write(f"| Previously Shortlisted (Cross-Day De-duplicated) | {previously_shortlisted_count} |\n")
        f.write(f"| Filtered Out (Senior/High Exp/Non-tech) | {skip_count - already_applied_count - previously_shortlisted_count} |\n")
        f.write(f"| **Total Verified Shortlisted (NEW IN 3-DAY WINDOW)** | **{len(shortlist_df)}** |\n")
        f.write(f"| — **Priority `APPLY` (0–1 Yr / Fresher / Junior)** | **{apply_count}** |\n")
        f.write(f"| — Reach `SHOT` (~2 Yrs / Portfolio Bridge) | {shot_count} |\n\n")

        f.write("### Platform Distribution\n\n")
        for site, cnt in merged_jobs['site'].value_counts().items():
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

if __name__ == "__main__":
    run_naukri_3_days()
