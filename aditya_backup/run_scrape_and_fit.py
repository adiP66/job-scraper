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

# Ensure cross-platform UTF-8 terminal encoding (prevents charmap crashes on Windows CMD)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, Exception):
        pass

def extract_experience_from_text(text: str) -> list[int]:
    """
    Thoroughly extracts all numeric experience requirements from a string (metadata or full JD).
    Handles markdown escapes, en-dashes, em-dashes, and formats like:
    - '6+ years', '6+ yrs', '6 + years'
    - '5 – 10 Yrs', '5 \\- 8 Yrs', '1-3 years', '2 to 5 yrs'
    - 'minimum 3 years', 'at least 2 yrs'
    - '6+ years of hands-on experience'
    - 'EXP- 4to 9 Years', 'experience: 3+ years'
    """
    if not text or pd.isna(text):
        return []
    
    # Strip all backslashes and normalize dashes
    cleaned = re.sub(r'\\+', '', str(text)).replace("–", "-").replace("—", "-")
    exp_nums = []

    for m in re.finditer(r'\b(\d+)\s*\+?\s*(?:years?|yrs?|yoe)\b', cleaned, re.I):
        exp_nums.append(int(m.group(1)))

    for m in re.finditer(r'(\d+)\s*(?:-|to)\s*(\d+)\s*(?:years?|yrs?)', cleaned, re.I):
        exp_nums.append(int(m.group(1)))
        exp_nums.append(int(m.group(2)))

    for m in re.finditer(r'(?:exp|experience)\s*(?:range)?\s*[:\-–—]\s*(\d+)', cleaned, re.I):
        exp_nums.append(int(m.group(1)))

    for m in re.finditer(r'(?:minimum|at\s+least|min\.?)\s*(?:of\s*)?(\d+)\s*(?:years?|yrs?)', cleaned, re.I):
        exp_nums.append(int(m.group(1)))

    for m in re.finditer(r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:\w+\s+){0,4}experience', cleaned, re.I):
        exp_nums.append(int(m.group(1)))

    for m in re.finditer(r'experience\s*(?:required)?\s*:\s*(\d+)', cleaned, re.I):
        exp_nums.append(int(m.group(1)))

    return exp_nums


def get_canonical_job_id_or_url(url: str) -> str:
    if not url or pd.isna(url):
        return ""
    u = str(url).strip()
    m_jk = re.search(r'[?&]jk=([a-zA-Z0-9]+)', u)
    if m_jk:
        return f"indeed:{m_jk.group(1)}"
    m_jl = re.search(r'[?&]jl=([a-zA-Z0-9]+)', u)
    if m_jl:
        return f"glassdoor:{m_jl.group(1)}"
    m_li = re.search(r'/jobs/view/(\d+)', u)
    if m_li:
        return f"linkedin:{m_li.group(1)}"
    m_nk = re.search(r'-(\d{10,})', u)
    if m_nk:
        return f"naukri:{m_nk.group(1)}"
    import urllib.parse
    parsed = urllib.parse.urlparse(u)
    return f"{parsed.netloc}{parsed.path}".rstrip("/").lower()


def _norm_text(s: str) -> str:
    if not s or pd.isna(s):
        return ""
    return re.sub(r'[^a-z0-9]', '', str(s).lower())


def load_applied_tracker() -> dict:
    tracker_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "applied_jobs.csv")
    tracker = {"ids": {}, "keys": {}}
    if os.path.exists(tracker_path):
        try:
            df = pd.read_csv(tracker_path, encoding="utf-8")
            for _, r in df.iterrows():
                raw_url = str(r.get("job_url") or "").strip()
                company = str(r.get("company") or "").strip()
                title = str(r.get("title") or "").strip()
                status = str(r.get("status") or "Applied")
                date = str(r.get("applied_date") or "")
                info = {"status": status, "date": date, "company": company, "title": title, "job_url": raw_url}
                cid = get_canonical_job_id_or_url(raw_url)
                if cid:
                    tracker["ids"][cid] = info
                if company and title and company.lower() != "nan":
                    tracker["keys"][(_norm_text(company), _norm_text(title))] = info
        except Exception as e:
            print(f"Warning loading applied tracker: {e}")
    return tracker


def evaluate_job(row: pd.Series, applied_tracker: dict = None) -> tuple[str, str, str]:
    """
    Evaluates a job listing against Aditya Parkhe's resume (BSc CS 2024, MSc AI 2026, 0-1 yr exp).
    Returns (tier, detected_exp_label, why).
    tier is one of: 'APPLY', 'SHOT', 'SKIP'.
    """
    title = str(row.get("title") or "").strip()
    company = str(row.get("company") or "").strip()
    job_url = str(row.get("job_url") or "").strip()
    exp_meta = str(row.get("experience_range") or "")
    desc = str(row.get("description") or "")
    skills = str(row.get("skills") or "")
    loc = str(row.get("location") or "")
    date_p = str(row.get("date_posted") or "")

    # Check if already applied using canonical ID and (company, title)
    if applied_tracker:
        cid = get_canonical_job_id_or_url(job_url)
        norm_k = (_norm_text(company), _norm_text(title))
        matched_info = None
        if cid and cid in applied_tracker.get("ids", {}):
            matched_info = applied_tracker["ids"][cid]
        elif norm_k in applied_tracker.get("keys", {}) and company.lower() != "nan":
            matched_info = applied_tracker["keys"][norm_k]
            
        if matched_info:
            return "SKIP", "Already Applied", f"Already applied on {matched_info.get('date', 'previously')} ({matched_info.get('status', 'Applied')})"
    
    # 0. Check Date Posted (Past 7 days only)
    if date_p and date_p != "nan":
        try:
            p_date = datetime.date.fromisoformat(date_p[:10])
            if p_date < (datetime.date.today() - datetime.timedelta(days=7)):
                return "SKIP", "Stale (>7d)", f"Job posted on {date_p} (older than 7 days)"
        except Exception:
            pass

    title_lower = title.lower()
    desc_lower = desc.lower()
    combined_text = f"{title_lower} {exp_meta.lower()} {skills.lower()} {desc_lower}"

    # 1. Senior / Lead Disqualification (Titles)
    senior_keywords = [
        "senior", "sr.", "sr ", "lead", "principal", "architect",
        "staff", "manager", "director", "head", "vp", "vice president", "president", "avp", "chief", "expert"
    ]
    for w in senior_keywords:
        if re.search(r'\b' + re.escape(w) + r'\b', title_lower):
            return "SKIP", "Senior Title", f"Job title explicitly indicates senior/lead level: '{title}'"

    # 2. Extract Experience Requirements from BOTH Metadata and Full JD
    meta_exps = extract_experience_from_text(exp_meta)
    jd_exps = extract_experience_from_text(desc)
    all_exps = meta_exps + jd_exps

    min_exp = min(all_exps) if all_exps else None
    max_exp = max(all_exps) if all_exps else None

    # 3. Explicit high-experience phrases in JD (e.g., '6+ years', '12 years', '5+ yrs', '3+ years')
    high_exp_match = re.search(r'\b([3-9]|\d{2,})\s*(?:\+)?\s*(?:years?|yrs?|yoe)\b', desc_lower, re.I)
    if high_exp_match:
        return "SKIP", f"{high_exp_match.group(1)}+ Yrs", f"JD explicitly demands {high_exp_match.group(0)} of experience"

    # 3b. Strict Location Filter (Mumbai MMR, Pune, or True Remote ONLY)
    loc_lower = loc.lower()
    banned_locations = [
        "bengaluru", "bangalore", "hyderabad", "chennai", "gurgaon", "gurugram",
        "noida", "delhi", "kolkata", "ahmedabad", "jaipur", "chandigarh", "kochi",
        "trivandrum", "coimbatore", "indore", "bhopal", "lucknow", "ka, in", "ts, in",
        "tn, in", "up, in", "pb, in", "wb, in", "dl, in", "hr, in", "karnataka", "telangana"
    ]
    if any(b in loc_lower for b in banned_locations):
        return "SKIP", "Location Excluded", f"Location outside target (Bangalore/Hyderabad/etc. strictly off-limits): '{loc}'"

    is_rem = bool(row.get("is_remote") == True or str(row.get("is_remote")).lower() == "true")
    wfh_type = str(row.get("work_from_home_type") or "").lower()
    is_remote_job = is_rem or any(k in loc_lower for k in ["remote", "wfh", "work from home"]) or "remote" in wfh_type or "remote" in title_lower

    if not is_remote_job:
        allowed_locations = ["mumbai", "navi mumbai", "thane", "pune", "maharashtra", "mh, in", "andheri", "powai", "mahape", "goregaon", "vikhroli", "kalyan"]
        if loc_lower and loc_lower not in ["nan", "india"] and not any(a in loc_lower for a in allowed_locations):
            return "SKIP", "Location Excluded", f"Location outside target (requires relocation): '{loc}'"

    # 4. Tech Stack Alignment with Aditya's Resume
    has_python = bool(re.search(r'\bpython\b', combined_text))
    has_fastapi = bool(re.search(r'\bfast\s*api\b', combined_text))
    has_rag_genai = any(bool(re.search(r'\b' + re.escape(w) + r'\b', combined_text)) for w in [
        "rag", "langchain", "langgraph", "vector", "chroma", "llm", "genai", "generative ai", "retrieval augmented"
    ])
    has_ml_dl = any(bool(re.search(r'\b' + re.escape(w) + r'\b', combined_text)) for w in [
        "deep learning", "machine learning", "pytorch", "tensorflow", "autogluon", "nlp", "computer vision", "xgboost"
    ])
    has_aws_cloud = any(bool(re.search(r'\b' + re.escape(w) + r'\b', combined_text)) for w in ["aws", "s3", "lambda", "redshift", "gcp", "azure"])
    has_sql_data = any(bool(re.search(r'\b' + re.escape(w) + r'\b', combined_text)) for w in ["postgresql", "duckdb", "sql", "etl", "data pipeline"])

    # Disqualify non-Python / non-AI irrelevant domains, quant, and prompt engineering
    irrelevant_roles = [
        "sales", "electrical", "company secretary", "sebi", "teacher", "civil", "mechanical", "servicenow",
        "social media", "marketing", "graphic designer", "graphic design", "content writer", "hr", "talent acquisition", "recruiter", "bpo", "telecaller",
        "quant", "quantitative", "prompt engineer", "prompt engineering", "prompt designer", "trader", "trading",
        "salesforce", "sap", "pega", "artist", "content creator", "video creator", "creator", "content operations",
        "market risk", "credit risk", "risk analyst", "exposure modelling", "geospatial",
        "java developer", "php", "laravel", "appian", "xsoar", "c++ developer", "c++ engineer", "workday"
    ]
    if any(re.search(r'\b' + re.escape(w) + r'\b', title_lower) for w in irrelevant_roles):
        return "SKIP", "Non-Target Domain", f"Role domain is outside target (quant/prompt eng/non-tech): '{title}'"

    quant_signals = ["hedge fund", "arbitrage", "ultra-low latency", "low latency trading", "hft", "order routing", "market data adapters"]
    if any(q in combined_text for q in quant_signals):
        return "SKIP", "Quant/HFT Domain", "JD matches quantitative hedge fund or low-latency trading infrastructure"

    # Blacklist known fake / ghost / training-institute / course-selling entities
    blacklisted_entities = [
        "dronestark", "t&m services", "t&m", "crossing infotech", "crossing info",
        "medinex workforce", "medinex", "nexal iit", "nexal"
    ]
    if any(b in company.lower() for b in blacklisted_entities):
        return "SKIP", "Blacklisted Entity", f"Company flagged/blacklisted: '{company}'"

    if not company or company.lower().strip() in ["", "nan", "none", "anonymous", "null"]:
        return "SKIP", "Anonymous Company", "Company name is hidden or blank (high ghost/scam risk)"

    scam_indicators = ["enroll for course", "training fee", "course fee", "pay for training", "security deposit"]
    if any(s in combined_text for s in scam_indicators):
        return "SKIP", "Training Scheme", "JD mentions course fees or enrollment requirements"

    if not (has_python or has_rag_genai or has_ml_dl or has_sql_data):
        return "SKIP", "Irrelevant Stack", "Core tech stack does not match Python or AI/ML"

    # 5. Check for Fresher / Entry-Level / Early-Career Indicators
    fresher_indicators = [
        "fresher", "freshers", "entry level", "entry-level", "graduate",
        "college graduate", "campus hiring", "trainee", "intern", "internship",
        "0-1 year", "0-1 yr", "0-2 years", "0-2 yrs", "0 to 1", "0 to 2", "0 yrs", "0 year"
    ]
    is_fresher = any(re.search(r'\b' + re.escape(w) + r'\b', combined_text) for w in fresher_indicators)
    is_junior_title = any(re.search(r'\b' + re.escape(w) + r'\b', title_lower) for w in [
        "junior", "jr.", "jr ", "associate", "trainee", "intern", "fresher"
    ])

    # 6. Build High-Relevance Reasons
    reasons = []
    if has_fastapi:
        reasons.append("FastAPI mentioned (direct match with UFC REST API project)")
    if has_rag_genai:
        reasons.append("RAG / LangChain / GenAI focus (direct match with Sports AI Analyst project)")
    if has_ml_dl:
        reasons.append("ML/DL focus (matches MSc AI + UFC ML research)")
    if has_aws_cloud:
        reasons.append("AWS / Cloud stack (matches AWS ETL pipeline project)")
    if has_sql_data:
        reasons.append("Database / SQL / Pipeline alignment")
    if not reasons and has_python:
        reasons.append(f"Core Python backend match for {title}")

    # 7. Strict Tier Assignment
    if min_exp is not None:
        if min_exp == 0:
            exp_label = "0 yrs"
            why_text = f"Explicitly requires 0 yrs (pure fresher fit); " + "; ".join(reasons)
            return "APPLY", exp_label, why_text
        elif min_exp in [1, 2]:
            exp_label = f"{min_exp}-{max_exp or (min_exp + 1)} Yrs"
            why_text = f"Reach opportunity: JD requires {min_exp}+ yrs experience; strong portfolio (predmma.in, LangGraph, FastAPI) can bridge the gap. Match: " + "; ".join(reasons)
            return "SHOT", exp_label, why_text
        else:
            return "SKIP", f"{min_exp}+ Yrs", f"JD requires {min_exp}+ years of experience (exceeds early-career profile)"
    else:
        if is_fresher or is_junior_title:
            exp_label = "Fresher/Junior"
            why_text = f"JD/Title explicitly indicates fresher or junior entry-level fit; " + "; ".join(reasons)
            return "APPLY", exp_label, why_text
        else:
            exp_label = "Unspecified"
            why_text = f"Experience requirement not stated in JD; verify mid-level expectations before applying. Match: " + "; ".join(reasons)
            return "SHOT", exp_label, why_text


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = f"scrape_{timestamp}"
    os.makedirs(folder, exist_ok=True)
    log_path = os.path.join(folder, "scrape.log")
    
    print(f"=== Starting Targeted Fresher Scrape into: {folder} ===")
    scraped_dfs = []
    
    # 1. JobSpy Streams (LinkedIn & Indeed) - Fresher & Junior specific
    print("\n--- 1. Scraping LinkedIn & Indeed (Targeted Fresher Queries) ---")
    jobspy_configs = [
        {"term": "python fresher", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "junior python developer", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "ai intern", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "machine learning intern", "loc": "Mumbai, Maharashtra", "wanted": 25},
        {"term": "generative ai intern", "loc": "India", "wanted": 20},
        {"term": "fastapi", "loc": "India", "wanted": 20},
        {"term": "backend developer fresher", "loc": "Mumbai, Maharashtra", "wanted": 20},
        {"term": "data analyst fresher", "loc": "Mumbai, Maharashtra", "wanted": 20},
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
            print(f"  -> Got {len(df_q)} jobs for '{cfg['term']}'")
            scraped_dfs.append(df_q)
        except Exception as e:
            print(f"  Error scraping JobSpy for '{cfg['term']}': {e}")

    # 2. Glassdoor Targeted Fresher Streams (Playwright Cloudflare-Bypass Engine)
    print("\n--- 2. Scraping Glassdoor (Playwright Cloudflare-Bypass Engine) ---")
    glassdoor_configs = [
        {"term": "python fresher", "loc": "Mumbai", "wanted": 25},
        {"term": "ai intern", "loc": "Mumbai", "wanted": 25},
        {"term": "junior python developer", "loc": "Mumbai", "wanted": 25},
        {"term": "machine learning intern", "loc": "Mumbai", "wanted": 20},
        {"term": "fastapi", "loc": "India", "wanted": 20},
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
        
    # 3. Naukri Targeted Fresher Streams (Playwright Akamai-Bypass Engine)
    print("\n--- 3. Scraping Naukri (Targeted Fresher & Early-Career Streams) ---")
    naukri_configs = [
        {"search_term": "python", "location": "Mumbai", "experience": 0, "wanted": 35, "label": "Python (Exp: 0 Yrs, Mumbai)"},
        {"search_term": "ai engineer fresher", "location": "Mumbai", "experience": None, "wanted": 30, "label": "AI Engineer Fresher (Mumbai)"},
        {"search_term": "python intern", "location": "Mumbai", "experience": None, "wanted": 30, "label": "Python Intern (Mumbai)"},
        {"search_term": "junior python developer", "location": "Mumbai", "experience": None, "wanted": 30, "label": "Junior Python Developer (Mumbai)"},
        {"search_term": "machine learning intern", "location": "Mumbai", "experience": None, "wanted": 30, "label": "ML Intern (Mumbai)"},
        {"search_term": "fastapi", "location": "Mumbai", "experience": 0, "wanted": 25, "label": "FastAPI (Exp: 0 Yrs, Mumbai)"},
        {"search_term": "generative ai", "location": "Mumbai", "experience": None, "wanted": 30, "label": "Generative AI (Mumbai)"},
        {"search_term": "machine learning", "location": "Mumbai", "experience": 0, "wanted": 30, "label": "Machine Learning (Exp: 0 Yrs, Mumbai)"},
        {"search_term": "backend developer fresher", "location": "Mumbai", "experience": None, "wanted": 30, "label": "Backend Developer Fresher (Mumbai)"},
        {"search_term": "data analyst fresher", "location": "Mumbai", "experience": None, "wanted": 30, "label": "Data Analyst Fresher (Mumbai)"},
        {"search_term": "python", "location": None, "experience": 0, "wanted": 25, "label": "Python (Exp: 0 Yrs, Pan-India)"},
        {"search_term": "ai engineer", "location": None, "experience": 0, "wanted": 25, "label": "AI Engineer (Exp: 0 Yrs, Pan-India)"},
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
            print(f"  -> Got {len(df_nk)} jobs for {cfg['label']}")
            scraped_dfs.append(df_nk)
        except Exception as e:
            print(f"  Error on Naukri stream '{cfg['label']}': {e}")

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

    # 3. Deep Evaluation against Resume & Full JD Text
    print("\n--- 3. Deep JD Evaluation against Aditya Parkhe's Resume ---")
    applied_tracker = load_applied_tracker()
    if applied_tracker:
        print(f"Loaded {len(applied_tracker['ids'])} already applied records to prevent duplicate recommendations.")

    shortlist_rows = []
    already_applied_list = []
    skip_count = 0
    already_applied_count = 0
    
    for _, row in all_jobs.iterrows():
        tier, exp_label, why = evaluate_job(row, applied_tracker=applied_tracker)
        
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

        if tier in ["APPLY", "SHOT"]:
            min_sal = row.get("min_amount")
            max_sal = row.get("max_amount")
            salary_str = "Not Disclosed"
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
        else:
            skip_count += 1

    df_shortlist = pd.DataFrame(shortlist_rows)
    if not df_shortlist.empty:
        df_shortlist.sort_values(by=["tier", "date_posted"], ascending=[True, False], inplace=True)

    shortlist_csv_path = os.path.join(folder, "apply_shortlist.csv")
    df_shortlist.to_csv(shortlist_csv_path, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False, encoding="utf-8")
    print(f"Saved shortlisted jobs to: {shortlist_csv_path}")
    apply_count = len(df_shortlist[df_shortlist['tier']=='APPLY']) if not df_shortlist.empty else 0
    shot_count = len(df_shortlist[df_shortlist['tier']=='SHOT']) if not df_shortlist.empty else 0
    print(f"Total Shortlisted: {len(df_shortlist)} (APPLY: {apply_count}, SHOT: {shot_count})")
    print(f"Total Filtered Out: {skip_count} (including {already_applied_count} already applied)")

    # 4. Markdown Report
    report_path = os.path.join(folder, "job_fit_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Targeted Fresher & Early-Career Job Fit Report\n\n")
        f.write(f"**Generated:** {datetime.date.today().strftime('%B %d, %Y')}\n\n")
        f.write(f"**Candidate:** Aditya Parkhe | MSc. AI (2026), BSc. CS (2024)\n")
        f.write(f"**Core Stack:** Python, FastAPI, RAG (LangChain/LangGraph/Chroma), Deep Learning/ML, AWS, PostgreSQL\n")
        f.write(f"**Freshness Window:** Verified Last 7 Days (Freshness Filters & Date Sorting Enforced)\n\n")
        f.write(f"---\n\n")
        
        f.write(f"## 1. Scraping & Pipeline Breakdown\n\n")
        f.write(f"| Metric | Count |\n|---|---|\n")
        f.write(f"| Total Raw Scraped | {len(all_jobs)} |\n")
        f.write(f"| Already Applied (De-duplicated) | {already_applied_count} |\n")
        f.write(f"| Filtered Out (Senior/High Exp/Non-tech) | {skip_count - already_applied_count} |\n")
        f.write(f"| **Total Verified Shortlisted (NEW)** | **{len(df_shortlist)}** |\n")
        f.write(f"| — **Priority `APPLY` (0–1 Yr / Fresher / Junior)** | **{apply_count}** |\n")
        f.write(f"| — Reach `SHOT` (~2 Yrs / Portfolio Bridge) | {shot_count} |\n\n")
        
        f.write(f"### Platform Distribution\n\n")
        for site_name, count in all_jobs["site"].value_counts().items():
            f.write(f"- **{site_name.capitalize()}:** {count} jobs\n")
            
        f.write(f"\n---\n\n")
        f.write(f"## 2. Priority Applications (`APPLY` Tier — 0 to 1 Year / Fresher / Junior Only)\n\n")
        if not df_shortlist.empty:
            apply_jobs = df_shortlist[df_shortlist["tier"] == "APPLY"]
            if apply_jobs.empty:
                f.write("No direct APPLY tier jobs found in this batch.\n\n")
            else:
                for _, j in apply_jobs.iterrows():
                    f.write(f"### {j['title']} — {j['company']}\n")
                    f.write(f"- **Source:** {j['site'].capitalize()} | **Posted:** {j['date_posted']} | **Location:** {j['location']}\n")
                    f.write(f"- **Experience Required:** `{j['experience_required']}` | **Salary:** {j['salary']}\n")
                    f.write(f"- **Job Link:** [{j['title']}]({j['job_url']})\n")
                    f.write(f"- **Why Apply:** {j['why']}\n\n")

        f.write(f"---\n\n")
        f.write(f"## 3. Stretch Opportunities (`SHOT` Tier — ~2 Years / Portfolio Bridge)\n\n")
        if not df_shortlist.empty:
            shot_jobs = df_shortlist[df_shortlist["tier"] == "SHOT"]
            if shot_jobs.empty:
                f.write("No SHOT tier jobs in this batch.\n\n")
            else:
                for _, j in shot_jobs.iterrows():
                    f.write(f"### {j['title']} — {j['company']}\n")
                    f.write(f"- **Source:** {j['site'].capitalize()} | **Posted:** {j['date_posted']} | **Location:** {j['location']}\n")
                    f.write(f"- **Experience Required:** `{j['experience_required']}` | **Salary:** {j['salary']}\n")
                    f.write(f"- **Job Link:** [{j['title']}]({j['job_url']})\n")
                    f.write(f"- **Why & Strategy:** {j['why']}\n\n")

        f.write(f"---\n\n")
        f.write(f"## 4. De-duplicated Jobs (Already Applied: {already_applied_count})\n\n")
        if already_applied_list:
            f.write(f"The following jobs were identified in this scrape but automatically de-duplicated because you have already applied to them:\n\n")
            f.write(f"| Company | Role | Platform | Application History |\n|---|---|---|---|\n")
            for aj in already_applied_list:
                f.write(f"| **{aj['company']}** | [{aj['title']}]({aj['job_url']}) | {aj['site'].capitalize()} | {aj['why']} |\n")
            f.write(f"\n")
        else:
            f.write(f"No previously applied jobs appeared in this scrape batch.\n\n")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"saving into: {folder}\n")
        f.write(f"TOTAL ROWS: {len(all_jobs)}\n")
        f.write(f"SHORTLISTED: {len(df_shortlist)}\n")
        f.write(f"APPLY: {apply_count}\n")
        f.write(f"SHOT: {shot_count}\n")
        f.write(all_jobs["site"].value_counts().to_string() + "\n")
        f.write("Completed successfully.\n")

    print(f"\nGenerated report: {report_path}")
    print(f"All files saved in: {folder}/")

if __name__ == "__main__":
    main()
