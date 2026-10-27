#!/usr/bin/env python3
"""
track_applications.py — Comprehensive Application & Follow-Up Ledger for Aditya Parkhe
Manages applied jobs, interview stages, follow-up deadlines, and outreach templates.
"""

import argparse
import datetime
import os
import sys
import pandas as pd

# Ensure cross-platform UTF-8 terminal encoding (prevents charmap crashes on Windows CMD)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

TRACKER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "applied_jobs.csv")

DEFAULT_COLUMNS = [
    "applied_date", "company", "title", "site", "location",
    "experience_required", "salary", "job_url", "status",
    "follow_up_date", "follow_up_status", "notes", "why"
]


def load_tracker() -> pd.DataFrame:
    if os.path.exists(TRACKER_FILE):
        try:
            df = pd.read_csv(TRACKER_FILE, encoding="utf-8")
            for col in DEFAULT_COLUMNS:
                if col not in df.columns:
                    if col == "follow_up_status":
                        df[col] = "Pending"
                    elif col == "notes":
                        df[col] = ""
                    elif col == "follow_up_date":
                        df[col] = df["applied_date"].apply(
                            lambda d: (datetime.date.fromisoformat(str(d)[:10]) + datetime.timedelta(days=5)).isoformat()
                            if pd.notna(d) and str(d)[:4].isdigit() else ""
                        )
                    else:
                        df[col] = ""
            for col in ["company", "title", "site", "status", "follow_up_status", "notes", "follow_up_date", "why", "location", "salary", "job_url"]:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str)
            return df
        except Exception as e:
            print(f"Error reading {TRACKER_FILE}: {e}")
    return pd.DataFrame(columns=DEFAULT_COLUMNS)


MASTER_TRACKER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "master_applied_jobs.csv")

def save_tracker(df: pd.DataFrame):
    df.to_csv(TRACKER_FILE, index=False, encoding="utf-8")
    df.to_csv(MASTER_TRACKER_FILE, index=False, encoding="utf-8")
    print(f"✅ Synchronized tracker ({len(df)} records) to:")
    print(f"   • {TRACKER_FILE}")
    print(f"   • {MASTER_TRACKER_FILE}")


def list_applications(df: pd.DataFrame, filter_status: str = None):
    if df.empty:
        print("No job applications recorded yet.")
        return
    
    view_df = df if not filter_status else df[df["status"].str.lower() == filter_status.lower()]
    print(f"\n{'='*100}")
    print(f"  JOB APPLICATION LEDGER ({len(view_df)} Applications)")
    print(f"{'='*100}")
    for idx, row in view_df.iterrows():
        status_tag = f"[{row.get('status', 'Applied').upper()}]"
        fu_tag = f"[Follow-Up: {row.get('follow_up_status', 'Pending')} ({row.get('follow_up_date', 'N/A')})]"
        print(f"{idx + 1:2d}. {status_tag:13s} {fu_tag:32s} | {row.get('applied_date', 'N/A')} | {row.get('company', '')} — {row.get('title', '')}")
        print(f"    Platform: {str(row.get('site', 'N/A')).capitalize()} | Location: {row.get('location', 'N/A')}")
        print(f"    URL: {row.get('job_url', '')}")
        notes = str(row.get("notes", "")).strip()
        if notes and notes != "nan":
            print(f"    📝 Notes: {notes}")
        print(f"{'-'*100}")


def show_follow_ups(df: pd.DataFrame):
    if df.empty:
        print("No applications to track follow-ups for.")
        return
    
    today = datetime.date.today()
    print(f"\n{'='*100}")
    print(f"  📅 APPLICATION FOLLOW-UP SCHEDULE (Today is {today.strftime('%B %d, %Y')})")
    print(f"{'='*100}")
    
    due_today = []
    overdue = []
    upcoming = []
    completed = []

    for idx, row in df.iterrows():
        fu_date_str = str(row.get("follow_up_date", "")).strip()
        fu_status = str(row.get("follow_up_status", "Pending")).strip()
        company = row.get("company", "")
        title = row.get("title", "")
        site = str(row.get("site", "")).capitalize()
        applied_date = row.get("applied_date", "")

        if fu_status.lower() in ["done", "followed up", "replied", "exempt", "disabled", "n/a", "not applicable"]:
            if fu_status.lower() in ["done", "followed up", "replied"]:
                completed.append((company, title, applied_date, fu_status))
            continue

        if not fu_date_str or fu_date_str == "nan":
            continue

        try:
            fu_date = datetime.date.fromisoformat(fu_date_str[:10])
            delta = (fu_date - today).days
            item = (company, title, site, applied_date, fu_date_str, delta, row.get("job_url", ""))
            if delta < 0:
                overdue.append(item)
            elif delta == 0:
                due_today.append(item)
            else:
                upcoming.append(item)
        except Exception:
            continue

    if due_today:
        print(f"\n🔴 DUE TODAY ({len(due_today)} applications ready for follow-up):")
        for comp, tit, site, app_d, fu_d, d, url in due_today:
            print(f"  • {comp} — {tit} (Applied: {app_d} on {site})")
            print(f"    Link: {url}")
    else:
        print("\n🟢 No follow-ups due exactly today.")

    if overdue:
        print(f"\n⚠️ OVERDUE ({len(overdue)} applications past follow-up date):")
        for comp, tit, site, app_d, fu_d, d, url in overdue:
            print(f"  • {comp} — {tit} (Due: {fu_d}, {-d} days ago | Applied: {app_d} on {site})")
            print(f"    Link: {url}")

    if upcoming:
        upcoming.sort(key=lambda x: x[5])  # Sort by days remaining
        print(f"\n🔵 UPCOMING FOLLOW-UPS ({len(upcoming)} scheduled):")
        for comp, tit, site, app_d, fu_d, d, url in upcoming:
            day_str = f"in {d} days" if d > 1 else "tomorrow"
            print(f"  • [{day_str:11s} | {fu_d}] {comp} — {tit} ({site})")

    if completed:
        print(f"\n✅ COMPLETED FOLLOW-UPS ({len(completed)} sent):")
        for comp, tit, app_d, status in completed:
            print(f"  • {comp} — {tit} (Status: {status})")
    
    print(f"\nTip: Run `python3 track_applications.py --template -c '<company>'` to generate a tailored LinkedIn outreach message.")
    print(f"{'='*100}")


def update_status(df: pd.DataFrame, company: str, new_status: str):
    matches = df[df["company"].str.contains(company, case=False, na=False)]
    if matches.empty:
        print(f"❌ No applications found matching company: '{company}'")
        return
    
    for idx in matches.index:
        old = df.at[idx, "status"]
        df.at[idx, "status"] = new_status
        print(f"🔄 Status Updated: {df.at[idx, 'company']} — {df.at[idx, 'title']}: {old} ➔ {new_status}")
    save_tracker(df)


def mark_followed_up(df: pd.DataFrame, company: str, status: str = "Followed Up"):
    matches = df[df["company"].str.contains(company, case=False, na=False)]
    if matches.empty:
        print(f"❌ No applications found matching company: '{company}'")
        return
    
    today_str = datetime.date.today().isoformat()
    for idx in matches.index:
        df.at[idx, "follow_up_status"] = status
        current_notes = str(df.at[idx, "notes"] or "")
        stamp = f"Followed up on {today_str}"
        if stamp not in current_notes:
            df.at[idx, "notes"] = f"{current_notes}; {stamp}".strip("; ")
        print(f"✅ Follow-up Recorded: {df.at[idx, 'company']} — {df.at[idx, 'title']} ({status})")
    save_tracker(df)


def add_note(df: pd.DataFrame, company: str, note_text: str):
    matches = df[df["company"].str.contains(company, case=False, na=False)]
    if matches.empty:
        print(f"❌ No applications found matching company: '{company}'")
        return
    
    today_str = datetime.date.today().isoformat()
    for idx in matches.index:
        current_notes = str(df.at[idx, "notes"] or "").strip()
        if current_notes and current_notes != "nan":
            df.at[idx, "notes"] = f"{current_notes} | [{today_str}] {note_text}"
        else:
            df.at[idx, "notes"] = f"[{today_str}] {note_text}"
        print(f"📝 Note Added to {df.at[idx, 'company']}: {df.at[idx, 'notes']}")
    save_tracker(df)


def set_follow_up_date(df: pd.DataFrame, company: str, new_date: str):
    matches = df[df["company"].str.contains(company, case=False, na=False)]
    if matches.empty:
        print(f"❌ No applications found matching company: '{company}'")
        return
    
    for idx in matches.index:
        df.at[idx, "follow_up_date"] = new_date
        print(f"📅 Follow-Up Date Set: {df.at[idx, 'company']} ➔ {new_date}")
    save_tracker(df)


def generate_template(df: pd.DataFrame, company: str):
    matches = df[df["company"].str.contains(company, case=False, na=False)]
    if matches.empty:
        print(f"❌ No applications found matching company: '{company}'")
        return
    
    row = matches.iloc[0]
    comp = row.get("company", "the team")
    title = row.get("title", "Software Engineer")
    applied_date = row.get("applied_date", "recently")
    site = str(row.get("site", "your job board")).capitalize()
    
    print(f"\n{'='*80}")
    print(f"  ✉️ TAILORED LINKEDIN OUTREACH MESSAGE FOR: {comp}")
    print(f"{'='*80}\n")
    
    print(f"Subject: Application Follow-up: {title} — Aditya Parkhe\n")
    print("--- Connection Request Note (<300 chars) ---")
    print(f"Hi [Recruiter Name], I recently applied for the {title} role at {comp}. As an MSc. AI candidate with production FastAPI & RAG agent experience (predmma.in), I'd love to connect and share how my background aligns with your engineering goals. Best, Aditya\n")
    
    print("--- InMail / Direct Message Template ---")
    print(f"Hi [Hiring Manager / Recruiter Name],\n")
    print(f"I hope you're having a great week.")
    print(f"I recently applied for the {title} position at {comp} on {applied_date} via {site}, and wanted to briefly reach out to introduce myself.\n")
    print(f"I am completing my MSc. in Artificial Intelligence (BSc. CS, 2024), specializing in backend engineering and applied AI systems. A few relevant highlights:")
    print(f"• Deployed live production systems including Pred MMA (predmma.in) with end-to-end FastAPI microservices.")
    print(f"• Built agentic RAG workflows using LangChain, LangGraph, and ChromaDB vector search.")
    print(f"• Designed automated cloud ETL pipelines on AWS (Lambda, S3, Redshift) and PostgreSQL.\n")
    print(f"I would welcome the opportunity to discuss how my skill set can support {comp}'s technical initiatives.")
    print(f"Resume & Portfolio: predmma.in | GitHub: github.com/adiP66\n")
    print(f"Thank you for your time and consideration,\nAditya Parkhe")
    print(f"{'='*80}\n")


def print_stats(df: pd.DataFrame):
    if df.empty:
        print("No applications recorded yet.")
        return
    print(f"\n📊 Applications Overview (Total: {len(df)}):")
    print(df["status"].value_counts().to_string())
    print("\nBy Follow-Up Status:")
    print(df["follow_up_status"].value_counts().to_string())
    print("\nBy Platform:")
    print(df["site"].value_counts().to_string())


def exempt_follow_up(df: pd.DataFrame, company_query: str, reason: str = "Enterprise MNC policy / direct cold outreach ineffective") -> pd.DataFrame:
    matched = df[df["company"].str.contains(company_query, case=False, na=False)]
    if matched.empty:
        print(f"No application found matching company: '{company_query}'")
        return df
    for idx in matched.index:
        df.loc[idx, "follow_up_status"] = "Exempt"
        df.loc[idx, "follow_up_date"] = ""
        current_notes = str(df.loc[idx, "notes"] or "").strip()
        note_to_add = f"Follow-up exempt ({reason})."
        if note_to_add not in current_notes:
            df.loc[idx, "notes"] = f"{current_notes} | {note_to_add}".strip(" | ")
        print(f"🚫 Disabled follow-up for: {df.loc[idx, 'company']} — {df.loc[idx, 'title']}")
    save_tracker(df)
    return df


def add_application(df: pd.DataFrame, company: str, title: str, site: str = "manual", location: str = "Mumbai", job_url: str = "", exp: str = "Fresher/Junior", salary: str = "Not Disclosed", why: str = "", notes: str = "") -> pd.DataFrame:
    today_str = datetime.date.today().isoformat()
    fu_date_str = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
    exists = df[(df["company"].str.lower() == company.lower().strip()) & (df["title"].str.lower() == title.lower().strip())]
    if not exists.empty:
        print(f"⚠️ Application already exists for {company} — {title}")
        return df
    new_entry = {
        "applied_date": today_str,
        "company": company.strip(),
        "title": title.strip(),
        "site": site.strip(),
        "location": location.strip(),
        "experience_required": exp.strip(),
        "salary": salary.strip(),
        "job_url": job_url.strip(),
        "status": "Applied",
        "why": why.strip(),
        "follow_up_date": fu_date_str,
        "follow_up_status": "Pending",
        "notes": notes.strip() or f"Applied on {today_str}."
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_tracker(df)
    print(f"✅ Added application: {company} — {title} (Follow-up scheduled for {fu_date_str})")
    return df


def main():
    parser = argparse.ArgumentParser(description="Aditya Parkhe's Job Application & Follow-Up Tracker")
    parser.add_argument("--list", "-l", action="store_true", help="List all applications")
    parser.add_argument("--follow-ups", "-f", action="store_true", help="Show follow-up schedule and deadlines")
    parser.add_argument("--status", "-s", type=str, help="Filter by status OR set new status if --company is provided")
    parser.add_argument("--company", "-c", type=str, help="Company name to target")
    parser.add_argument("--add", "-a", action="store_true", help="Add a new applied job (requires -c and -j/--title)")
    parser.add_argument("--title", "-j", type=str, help="Job title for --add")
    parser.add_argument("--url", "-u", type=str, default="", help="Job URL for --add")
    parser.add_argument("--site", type=str, default="manual", help="Platform/site for --add (e.g. linkedin, naukri)")
    parser.add_argument("--location", type=str, default="Mumbai", help="Location for --add")
    parser.add_argument("--exp", type=str, default="Fresher/Junior", help="Experience requirement for --add")
    parser.add_argument("--followed-up", action="store_true", help="Mark follow-up as sent for target company")
    parser.add_argument("--exempt-follow-up", action="store_true", help="Mark follow-up as exempt for enterprise companies")
    parser.add_argument("--note", "-n", type=str, help="Add a note for target company")
    parser.add_argument("--set-follow-up", type=str, help="Set specific follow-up date (YYYY-MM-DD)")
    parser.add_argument("--template", "-t", action="store_true", help="Generate tailored LinkedIn message template")
    parser.add_argument("--email", "-m", action="store_true", help="Discover contact email and generate tailored cold email draft")
    parser.add_argument("--stats", action="store_true", help="Show summary statistics")

    args = parser.parse_args()
    df = load_tracker()
    if args.add:
        if not args.company or not args.title:
            print("❌ Error: Both --company (-c) and --title (-t) are required when adding an application.")
            sys.exit(1)
        add_application(
            df,
            company=args.company,
            title=args.title,
            site=args.site,
            location=args.location,
            job_url=args.url,
            exp=args.exp,
            notes=args.note or ""
        )
    elif args.company:
        if args.status:
            update_status(df, args.company, args.status)
        elif getattr(args, "followed_up", False):
            mark_followed_up(df, args.company)
        elif getattr(args, "exempt_follow_up", False):
            exempt_follow_up(df, args.company)
        elif args.set_follow_up:
            set_follow_up_date(df, args.company, args.set_follow_up)
        elif args.note:
            add_note(df, args.company, args.note)
        elif args.email:
            try:
                from find_contact_and_draft_email import process_company
                process_company(args.company)
            except Exception as e:
                print(f"Error generating email: {e}")
        elif args.template:
            generate_template(df, args.company)
        else:
            list_applications(df[df["company"].str.contains(args.company, case=False, na=False)])
    elif args.follow_ups:
        show_follow_ups(df)
    elif args.stats:
        print_stats(df)
    else:
        list_applications(df, filter_status=args.status)


if __name__ == "__main__":
    main()
