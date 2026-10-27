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
    folder = f"scrape_{timestamp}_deep"
    os.makedirs(folder, exist_ok=True)
    today_str = str(datetime.date.today())

    print(f"=== Starting Specialized Deep AI/ML Scrape into: {folder} ===")
    scraped_dfs = []

    # 1. JobSpy Streams (LinkedIn & Indeed) - Advanced AI & Stack Queries
    print("\n--- 1. Scraping LinkedIn & Indeed (Deep AI/ML/Agentic Queries) ---")
    jobspy_configs = [
        {"term": "langchain", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "langchain", "loc": "India", "wanted": 25},
        {"term": "ai agent", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "ai agent", "loc": "India", "wanted": 25},
        {"term": "llm engineer", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "llm engineer", "loc": "India", "wanted": 25},
        {"term": "fastapi", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "pytorch", "loc": "Mumbai, Maharashtra", "wanted": 20},
        {"term": "pytorch", "loc": "India", "wanted": 20},
        {"term": "rag ai", "loc": "India", "wanted": 20},
        {"term": "python backend developer", "loc": "Mumbai, Maharashtra", "wanted": 25},
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
        except Exception as e:
            print(f"  Error scraping JobSpy for '{cfg['term']}': {e}")

    # 2. Glassdoor Targeted Deep Streams
    print("\n--- 2. Scraping Glassdoor (Specialized AI/LLM/FastAPI Streams) ---")
    glassdoor_configs = [
        {"term": "langchain", "loc": "Mumbai", "wanted": 25},
        {"term": "ai agent", "loc": "Mumbai", "wanted": 25},
        {"term": "llm", "loc": "Mumbai", "wanted": 25},
        {"term": "fastapi", "loc": "Mumbai", "wanted": 25},
        {"term": "pytorch", "loc": "Mumbai", "wanted": 25},
        {"term": "generative ai", "loc": "Mumbai", "wanted": 25},
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
        except Exception as e:
            print(f"  Error scraping Glassdoor for '{cfg['term']}': {e}")

    # 3. Naukri Deep AI Streams
    print("\n--- 3. Scraping Naukri (Deep AI & Framework Streams) ---")
    naukri_configs = [
        {"search_term": "langchain", "location": "Mumbai", "experience": None, "wanted": 30, "label": "LangChain (Mumbai)"},
        {"search_term": "langchain", "location": None, "experience": 0, "wanted": 25, "label": "LangChain (Exp: 0, Pan-India)"},
        {"search_term": "ai agent", "location": "Mumbai", "experience": None, "wanted": 30, "label": "AI Agent (Mumbai)"},
        {"search_term": "llm engineer", "location": "Mumbai", "experience": None, "wanted": 30, "label": "LLM Engineer (Mumbai)"},
        {"search_term": "llm engineer", "location": "Pune", "experience": None, "wanted": 25, "label": "LLM Engineer (Pune)"},
        {"search_term": "fastapi", "location": "Mumbai", "experience": None, "wanted": 30, "label": "FastAPI (Mumbai)"},
        {"search_term": "pytorch", "location": "Mumbai", "experience": None, "wanted": 30, "label": "PyTorch (Mumbai)"},
        {"search_term": "pytorch", "location": "Pune", "experience": None, "wanted": 25, "label": "PyTorch (Pune)"},
        {"search_term": "rag", "location": "Mumbai", "experience": None, "wanted": 30, "label": "RAG (Mumbai)"},
        {"search_term": "generative ai developer", "location": "Mumbai", "experience": None, "wanted": 30, "label": "GenAI Developer (Mumbai)"},
        {"search_term": "generative ai developer", "location": "Pune", "experience": None, "wanted": 25, "label": "GenAI Developer (Pune)"},
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
            )
            print(f"  -> Got {len(df_nk)} jobs from Naukri for '{cfg['label']}'")
            if not df_nk.empty:
                scraped_dfs.append(df_nk)
        except Exception as e:
            print(f"  Error scraping Naukri for '{cfg['label']}': {e}")

    if not scraped_dfs:
        print("No jobs scraped in deep scrape.")
        return

    all_jobs = pd.concat(scraped_dfs, ignore_index=True)
    all_jobs.drop_duplicates(subset=["job_url"], keep="first", inplace=True)
    print(f"\nTotal raw jobs collected: {len(all_jobs)}")
    print(all_jobs["site"].value_counts())

    raw_jobs_path = os.path.join(folder, "jobs.csv")
    all_jobs.to_csv(raw_jobs_path, index=False)
    print(f"Saved raw jobs to: {raw_jobs_path}")

    # Evaluate
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
            # Cross portal deduplication guard
            comp = str(row.get("company") or "").lower()
            if "bytepadna" in comp:
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

    # Markdown Report
    report_path = os.path.join(folder, "job_fit_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Deep AI/ML Specialized Job Fit Report\n\n")
        f.write(f"**Generated:** {datetime.date.today().strftime('%B %d, %Y')}\n\n")
        f.write(f"**Candidate:** Aditya Parkhe | MSc. AI (2026), BSc. CS (2024)\n")
        f.write(f"**Core Stack Focus:** LangChain, LangGraph, RAG, PyTorch, FastAPI, AI Agents, LLM Engineering\n\n")
        f.write(f"| Metric | Count |\n|---|---|\n")
        f.write(f"| Total Raw Scraped | {len(all_jobs)} |\n")
        f.write(f"| Already Applied / De-duplicated | {already_applied_count} |\n")
        f.write(f"| Previously Shortlisted | {previously_shortlisted_count} |\n")
        f.write(f"| Filtered Out (Senior/Off-limits) | {filtered_other} |\n")
        f.write(f"| **Verified Shortlisted** | **{len(df_shortlist)}** |\n")
        f.write(f"| — Priority `APPLY` | **{apply_count}** |\n")
        f.write(f"| — Reach `SHOT` | {shot_count} |\n\n")

        apply_jobs = df_shortlist[df_shortlist["tier"] == "APPLY"] if not df_shortlist.empty else pd.DataFrame()
        f.write("## 1. Priority Applications (`APPLY` Tier — 0 to 1 Year / Fresher / Junior Only)\n\n")
        if apply_jobs.empty:
            f.write("No new direct APPLY tier jobs found in this deep pass.\n\n")
        else:
            for _, j in apply_jobs.iterrows():
                f.write(f"### {j['title']} — {j['company']}\n")
                f.write(f"- **Source:** {str(j['site']).capitalize()} | **Location:** {j['location']}\n")
                f.write(f"- **Experience:** {j['experience_required']}\n")
                f.write(f"- **Fit Reason:** {j['why']}\n")
                f.write(f"- **URL:** [Apply Here]({j['job_url']})\n\n")

        shot_jobs = df_shortlist[df_shortlist["tier"] == "SHOT"] if not df_shortlist.empty else pd.DataFrame()
        f.write("## 2. Worth a Shot (`SHOT` Tier — Early-Career / Startup Reach)\n\n")
        if shot_jobs.empty:
            f.write("No new SHOT tier jobs found in this deep pass.\n\n")
        else:
            for _, j in shot_jobs.iterrows():
                f.write(f"### {j['title']} — {j['company']}\n")
                f.write(f"- **Source:** {str(j['site']).capitalize()} | **Location:** {j['location']}\n")
                f.write(f"- **Experience:** {j['experience_required']}\n")
                f.write(f"- **Fit Reason:** {j['why']}\n")
                f.write(f"- **URL:** [Apply Here]({j['job_url']})\n\n")

    print(f"Generated report: {report_path}")

if __name__ == "__main__":
    main()
