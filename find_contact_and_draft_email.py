#!/usr/bin/env python3
"""
find_contact_and_draft_email.py — Automated Email Discovery & Customized Outreach Drafter
Designed for Aditya Parkhe (MSc. AI, BSc. CS, predmma.in)
Finds contact emails (HR, Managing Engineers, Talent Teams) for target companies
and generates tailored, high-signal cold outreach email drafts.
"""

import argparse
import glob
import os
import re
import sys
import urllib.parse
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
DRAFTS_DIR = os.path.join(WORKSPACE_DIR, "outreach_drafts")
os.makedirs(DRAFTS_DIR, exist_ok=True)

CANDIDATE = {
    "name": "Aditya Parkhe",
    "degree": "MSc. in Artificial Intelligence (BSc. CS, 2024)",
    "phone": "+91 99875 68753",
    "email": "parkheaditya01@gmail.com",
    "portfolio": "https://predmma.in",
    "github": "https://github.com/adiP66",
    "linkedin": "https://linkedin.com/in/adityaparkhe",
    "core_stack": ["Python", "FastAPI", "RAG (LangChain / LangGraph)", "ChromaDB", "Deep Learning", "PostgreSQL"],
    "live_project": "Pred MMA (predmma.in) — end-to-end FastAPI microservices and machine learning fight prediction platform",
}

KNOWN_DOMAINS = {
    "lexsi": "lexsi.ai",
    "revvity": "revvity.com",
    "cursor": "cursor.com",
    "bharatgen": "bharatgen.in",
    "craticai": "cratic.ai",
    "vlink": "vlinkinfo.com",
    "indiafilings": "indiafilings.com",
    "india filings": "indiafilings.com",
    "raysoft": "raysoft.ai",
    "tranzily": "tranzily.com",
    "fluidai": "fluid.ai",
    "fluid ai": "fluid.ai",
    "netcore": "netcorecloud.com",
    "metaminds": "metaminds.studio",
    "emburc": "emburc.com",
    "blackrock": "blackrock.com",
    "artcode": "artcodetech.com",
    "ambak": "ambak.com",
    "npci": "npci.org.in",
    "national payments": "npci.org.in",
    "linedata": "linedata.com",
    "adoraxe": "adoraxe.com",
    "pixeldust": "pixeldust.in",
    "bharat24by7": "bharat24by7.com",
    "discovr": "discovr.ai",
    "yodaplus": "yodaplus.com",
    "emkay": "emkayglobal.com",
    "nelson": "nelsoninfotech.com",
    "munich re": "munichre.com",
    "ventura": "venturasecurities.com",
    "jiosaavn": "jiosaavn.com",
    "ternuvo": "ternuvo.ai",
    "stackbinary": "stackbinary.io",
    "recollia": "recollia.ai",
    "mahashankh": "mahashankh.com",
    "volody": "volody.com",
    "purplle": "purplle.com",
    "kodo": "kodo.com",
    "fractal": "fractal.ai",
    "jpmorgan": "jpmorganchase.com",
    "wsp": "wsp.com",
    "asian paints": "asianpaints.com",
    "optum": "optum.com",
    "saama": "saama.com",
    "suiteguru": "suiteguru.com",
    "edwise": "edwiseinternational.com",
    "seawind": "seawindsolution.com",
    "datafuel": "datafuel.tech",
    "acies": "acies.holdings",
    "abbott": "abbott.com",
    "morningstar": "morningstar.com",
    "failte energy": "failteenergy.com",
}


def extract_emails_from_text(text: str) -> List[str]:
    """Extracts valid email addresses from raw text."""
    if not text or not isinstance(text, str):
        return []
    raw_matches = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    valid = []
    ignored_exts = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf", ".css", ".js")
    ignored_domains = ("example.com", "domain.com", "yourcompany.com", "sentry.io", "w3.org", "company.com", "email.com")
    ignored_prefixes = ("dataprotectionofficer", "privacy", "abuse", "postmaster", "test")

    for em in raw_matches:
        em_clean = em.rstrip(".,;:)").lower().strip()
        if em_clean.endswith(ignored_exts):
            continue
        domain = em_clean.split("@")[-1]
        prefix = em_clean.split("@")[0]
        if domain in ignored_domains or prefix in ignored_prefixes:
            continue
        tld = domain.split(".")[-1]
        if len(tld) >= 2 and tld.isalpha():
            if em_clean not in valid:
                valid.append(em_clean)
    return valid


def infer_domain(company_name: str) -> str:
    """Infers the primary domain for a company name."""
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", company_name).lower().strip()
    clean = clean.replace("pvt ltd", "").replace("private limited", "").replace("technologies", "").replace("solutions", "").strip()

    for k, dom in KNOWN_DOMAINS.items():
        if k in clean:
            return dom

    slug = clean.replace(" ", "")
    return f"{slug}.com"


def scrape_website_for_contacts(domain: str) -> List[str]:
    """Proactively checks official website pages (/contact, /careers, /about) for emails."""
    if not domain or domain.endswith("example.com"):
        return []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    found_emails = []
    subpaths = ["", "/contact", "/contact-us", "/careers", "/about", "/team"]
    
    base = f"https://www.{domain}" if not domain.startswith("http") else domain
    for p in subpaths:
        target = f"{base.rstrip('/')}{p}"
        try:
            resp = requests.get(target, headers=headers, timeout=5)
            if resp.status_code == 200:
                extracted = extract_emails_from_text(resp.text)
                for e in extracted:
                    if domain.split(".")[0] in e:
                        if e not in found_emails:
                            found_emails.append(e)
        except Exception:
            continue
    return found_emails


def search_web_for_hr_or_engineer(company: str, domain: str = "") -> List[str]:
    """Searches DuckDuckGo HTML for HR, Talent Lead, or Engineering Manager contacts."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    found = []
    queries = [
        f'"{company}" ("careers" OR "contact" OR "hr") email',
        f'"{company}" ("Engineering Manager" OR "Head of AI" OR "Tech Recruiter" OR "HR")'
    ]
    for q in queries:
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
            resp = requests.post(
                "https://html.duckduckgo.com/html/",
                data={"q": q},
                headers=headers,
                timeout=5
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                snippets = [s.get_text() for s in soup.find_all("a", class_="result__snippet")]
                for snip in snippets:
                    emails = extract_emails_from_text(snip)
                    for e in emails:
                        if domain and domain.split(".")[0] in e:
                            if e not in found:
                                found.append(e)
                        elif any(k in e for k in ["careers", "talent", "hr", "jobs", "recruiting", "hiring"]):
                            if e not in found:
                                found.append(e)
        except Exception:
            continue
    return found


def discover_all_emails(company: str, jd_text: str = "", domain: str = "") -> Dict[str, List[str]]:
    """Aggregates emails from JD, website crawl, web search, and standard inboxes."""
    inferred_domain = domain or infer_domain(company)
    results = {
        "direct_from_jd": extract_emails_from_text(jd_text),
        "from_website": scrape_website_for_contacts(inferred_domain),
        "from_web_search": search_web_for_hr_or_engineer(company, inferred_domain),
        "standard_inboxes": [
            f"careers@{inferred_domain}",
            f"talent@{inferred_domain}",
            f"hr@{inferred_domain}",
            f"jobs@{inferred_domain}"
        ]
    }
    return results


def generate_cold_outreach_email(company: str, title: str = "Software Engineer", target_email: str = "", recipient_name: str = "Hiring Team") -> Dict[str, str]:
    """Generates a high-signal, tailored 3-paragraph cold application email."""
    title_lower = title.lower()
    is_genai = any(k in title_lower for k in ["ai", "genai", "generative", "agent", "llm", "machine learning"])
    is_backend = any(k in title_lower for k in ["python", "backend", "fastapi", "django", "developer", "engineer"])

    if is_genai:
        subject = f"MSc. AI Engineer & Live RAG Builder — Application for {title} — Aditya Parkhe"
        p2_highlight = (
            "Over the past year, I've focused on building production-grade AI and agentic systems. "
            "I recently deployed Pred MMA (https://predmma.in), an end-to-end FastAPI and machine learning platform, "
            "and built multi-step RAG workflows with LangChain, LangGraph, and ChromaDB vector search. "
            "My master's thesis research directly centers on Deep Learning and LLM orchestration."
        )
    elif is_backend:
        subject = f"FastAPI & Python Backend Engineer — Application for {title} — Aditya Parkhe"
        p2_highlight = (
            "I specialize in scalable backend architectures and data pipelines. "
            "I built and maintain Pred MMA (https://predmma.in) in live production using FastAPI, PostgreSQL, and AWS (Lambda/S3), "
            "achieving high-throughput low-latency REST endpoints. I also design automated ETL workflows and microservices."
        )
    else:
        subject = f"Software Engineer Application for {title} — Aditya Parkhe"
        p2_highlight = (
            "I build production software systems in Python and modern frameworks. "
            "I architected and maintain Pred MMA (https://predmma.in) with FastAPI, PostgreSQL, and AWS, "
            "and build resilient data pipelines and automated workflows."
        )

    salutation = f"Hi {recipient_name}," if recipient_name and recipient_name != "Hiring Team" else "Hi Team,"

    body = (
        f"{salutation}\n\n"
        f"I hope you're having a productive week.\n\n"
        f"I noticed {company}'s opening for the {title} role and wanted to reach out directly to express my strong interest in joining your engineering team.\n\n"
        f"{p2_highlight}\n\n"
        f"What excites me about {company} is the opportunity to contribute clean, production-ready code from day one. "
        f"I'm completing my MSc. in Artificial Intelligence (BSc. Computer Science, 2024), and I prioritize shipping practical, reliable software over hypothetical prototypes.\n\n"
        f"A quick look at my work:\n"
        f"• Live Production System: https://predmma.in\n"
        f"• GitHub & Open Source: https://github.com/adiP66\n"
        f"• LinkedIn: https://linkedin.com/in/adityaparkhe\n\n"
        f"I would welcome 10–15 minutes to discuss how my skill set in Python, FastAPI, and applied AI can support {company}'s current initiatives. I've attached my resume for your review.\n\n"
        f"Thank you for your time and consideration,\n\n"
        f"Aditya Parkhe\n"
        f"MSc. Artificial Intelligence | BSc. Computer Science\n"
        f"Portfolio: predmma.in | GitHub: github.com/adiP66 | Phone: +91 99875 68753\n"
        f"Mumbai, Maharashtra, India\n"
    )

    mailto_params = urllib.parse.urlencode({"subject": subject, "body": body}, quote_via=urllib.parse.quote)
    mailto_url = f"mailto:{target_email}?{mailto_params}" if target_email else f"mailto:?{mailto_params}"

    return {
        "subject": subject,
        "body": body,
        "mailto_url": mailto_url,
        "to_email": target_email
    }


def process_company(company: str, title: str = "", jd_text: str = "", email_override: str = "", recipient_override: str = "") -> Dict:
    """Full pipeline to discover contact emails and generate tailored draft."""
    print(f"\n{'='*70}")
    print(f"  🔍 DISCOVERING CONTACT & GENERATING OUTREACH: {company}")
    print(f"{'='*70}")
    
    contacts = discover_all_emails(company, jd_text)
    primary_email = email_override
    if not primary_email:
        if contacts["direct_from_jd"]:
            primary_email = contacts["direct_from_jd"][0]
        elif contacts["from_website"]:
            primary_email = contacts["from_website"][0]
        elif contacts["from_web_search"]:
            primary_email = contacts["from_web_search"][0]
        else:
            primary_email = contacts["standard_inboxes"][0]

    rec_name = recipient_override or "Hiring Team"
    draft = generate_cold_outreach_email(company, title=title or "AI / Software Engineer", target_email=primary_email, recipient_name=rec_name)

    slug = re.sub(r"[^a-zA-Z0-9]", "_", company.lower()).strip("_")
    draft_path = os.path.join(DRAFTS_DIR, f"{slug}.txt")
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(f"TO: {primary_email}\n")
        f.write(f"SUBJECT: {draft['subject']}\n")
        f.write(f"MAILTO LINK: {draft['mailto_url']}\n")
        f.write("-" * 60 + "\n\n")
        f.write(draft["body"])

    print(f"• Company: {company} | Role: {title or 'AI / Software Engineer'}")
    print(f"• Primary Contact Target: {primary_email}")
    print(f"• Direct from JD: {contacts['direct_from_jd'] or 'None'}")
    print(f"• Found on Website: {contacts['from_website'] or 'None'}")
    print(f"• Found via Search: {contacts['from_web_search'] or 'None'}")
    print(f"• Saved draft to: {os.path.relpath(draft_path, WORKSPACE_DIR)}")

    return {
        "company": company,
        "title": title,
        "primary_email": primary_email,
        "all_emails": contacts,
        "draft_path": draft_path,
        "mailto_url": draft["mailto_url"]
    }


def main():
    parser = argparse.ArgumentParser(description="Automated Email Discovery & Cold Outreach Drafter")
    parser.add_argument("--company", "-c", type=str, help="Company name to find emails and draft outreach for")
    parser.add_argument("--title", "-t", type=str, default="AI / Software Engineer", help="Job title")
    parser.add_argument("--email", "-e", type=str, default="", help="Manually override target email")
    parser.add_argument("--name", "-n", type=str, default="", help="Hiring Manager / HR recipient name")
    parser.add_argument("--shortlist", "-s", type=str, help="Path to apply_shortlist.csv to batch process priority roles")
    args = parser.parse_args()

    if args.company:
        process_company(args.company, title=args.title, email_override=args.email, recipient_override=args.name)
    elif args.shortlist:
        if os.path.exists(args.shortlist):
            df = pd.read_csv(args.shortlist)
            prio = df[df["tier"] == "APPLY"]
            for idx, r in prio.iterrows():
                process_company(r["company"], title=r.get("title", ""), jd_text=str(r.get("why", "")))
        else:
            print(f"File not found: {args.shortlist}")
    else:
        print("Specify --company '<name>' or --shortlist '<path/to/apply_shortlist.csv>'")


if __name__ == "__main__":
    main()
