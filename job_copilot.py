#!/usr/bin/env python3
# AI Job Search Copilot — OpenAI-only + TF-IDF scoring + robust CSV + resilient summary

import os
import re
import csv
import argparse
import pathlib
import requests
from datetime import datetime
from typing import List, Dict

# --- env + scoring deps ---
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()  # reads .env (OPENAI_API_KEY, OPENAI_MODEL, etc.)

# --- Agent (Agno) with OpenAI ---
from agno.agent import Agent
from agno.models.openai import OpenAIChat


# =========================
# Agent & Prompt
# =========================
def make_agent() -> Agent:
    """Uses OpenAI GPT model based on env var OPENAI_MODEL (default: gpt-4o-mini)."""
    model = OpenAIChat(id=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    return Agent(
        model=model,
        instructions=(
            "You are a concise, practical career assistant for Data/Analytics roles. "
            "Given a RESUME and a JOB:\n"
            "1) Extract must-have skills (SQL, Python, BI, statistics, cloud, ETL) and business outcomes.\n"
            "2) Map resume achievements to those requirements using concrete metrics (%, time saved, revenue, latency).\n"
            "3) Output two Markdown sections:\n"
            "   ## Tailored Resume Summary (120–160 words, ATS-friendly, 3–5 bullet points w/ metrics)\n"
            "   ## Cover Letter (220–320 words, specific to the company; avoid generic buzzwords)\n"
            "Be honest (no fabrications). Prefer measurable impact."
        )
    )


def make_prompt(resume_text: str, job: Dict) -> str:
    return (
        f"RESUME:\n{resume_text}\n\n"
        f"JOB:\nTitle: {job.get('title','')}\nCompany: {job.get('company','')}\n"
        f"Location: {job.get('location','')}\nURL: {job.get('url','')}\n"
        f"Description:\n{job.get('description','')}\n\n"
        "TASK: Produce the two Markdown sections exactly in this order:\n"
        "## Tailored Resume Summary\n(120–160 words; use 3–5 bullets with metrics where helpful)\n\n"
        "## Cover Letter\n(220–320 words; be specific to this company and role)"
    )


# =========================
# Fetchers
# =========================
def fetch_remotive(role: str) -> List[Dict]:
    """Fetch jobs from Remotive public API and filter by role in title/tags."""
    url = "https://remotive.com/api/remote-jobs"
    try:
        data = requests.get(url, timeout=20).json()
        jobs = data.get("jobs", [])
        out = []
        role_l = role.lower()
        for x in jobs:
            title = x.get("title", "") or ""
            tags = " ".join(x.get("tags") or []) if isinstance(x.get("tags"), list) else str(x.get("tags") or "")
            if role_l in (title + " " + tags).lower():
                out.append({
                    "source": "remotive",
                    "title": title,
                    "company": x.get("company_name", "") or "",
                    "location": x.get("candidate_required_location", "Remote") or "Remote",
                    "url": x.get("url", "") or "",
                    "description": x.get("description", "") or "",
                })
        return out
    except Exception:
        return []


def fetch_remoteok(role: str) -> List[Dict]:
    """Fetch jobs from RemoteOK public API and filter by role in title."""
    url = "https://remoteok.com/api"
    try:
        data = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}).json()
        out = []
        role_l = role.lower()
        if isinstance(data, list):
            for x in data:
                if not isinstance(x, dict):
                    continue
                title = x.get("position") or x.get("role") or x.get("title") or ""
                if title and role_l in title.lower():
                    desc_html = x.get("description", "") or ""
                    desc = re.sub(r"<.*?>", "", desc_html)  # strip HTML
                    out.append({
                        "source": "remoteok",
                        "title": title,
                        "company": x.get("company", "") or "",
                        "location": (x.get("location") or "Remote"),
                        "url": ("https://remoteok.com" + x.get("url", "")) if x.get("url") else "",
                        "description": desc,
                    })
        return out
    except Exception:
        return []


# =========================
# Helpers
# =========================
def filter_jobs(jobs: List[Dict], location: str) -> List[Dict]:
    if location:
        loc_l = location.lower()
        jobs = [
            j for j in jobs
            if loc_l in (j.get("location", "") + " " + j.get("title", "") + " " + j.get("company", "")).lower()
        ]
    # dedupe by (title, company)
    seen, uniq = set(), []
    for j in jobs:
        key = (j.get("title", "").strip(), j.get("company", "").strip())
        if key not in seen:
            seen.add(key)
            uniq.append(j)
    return uniq


def score_job(resume_text: str, job_desc: str) -> float:
    """Return cosine similarity 0..1 between resume and job description."""
    docs = [resume_text, job_desc or ""]
    tfidf = TfidfVectorizer(stop_words="english", max_features=4000)
    X = tfidf.fit_transform(docs)
    return float(cosine_similarity(X[0], X[1])[0, 0])


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def save_jobs_csv(rows: List[Dict], path: pathlib.Path, mode: str = "w") -> None:
    """
    mode='w' => overwrite with header
    mode='a' => append rows; writes header only if file didn't exist
    If the CSV is locked (opened in Excel), writes to a timestamped file instead.
    """
    if not rows:
        return
    fields = ["source", "title", "company", "location", "url", "score"]

    try:
        exists = path.exists()
        write_mode = "a" if mode == "a" else "w"
        with open(path, write_mode, newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            if write_mode == "w" or not exists:
                w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in fields})
    except PermissionError:
        # file is open elsewhere — write to a timestamped fallback
        alt = path.with_name(f"{path.stem}_{datetime.now():%Y%m%d_%H%M%S}{path.suffix}")
        with open(alt, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in fields})
        print(f"CSV locked by another program; wrote to {alt}")


# =========================
# Main
# =========================
def main():
    parser = argparse.ArgumentParser(description="AI Job Search Copilot (OpenAI + TF-IDF ranking)")
    parser.add_argument("--role", required=True, help='Target role, e.g. "Data Analyst"')
    parser.add_argument("--location", default="", help='Location keyword filter, e.g. "Remote" or "Toronto"')
    parser.add_argument("--count", type=int, default=20, help="Max raw jobs to fetch before scoring")
    parser.add_argument("--top-k", type=int, default=5, help="Generate letters for the top-K scored jobs")
    parser.add_argument("--min-score", type=float, default=0.12, help="Keep only jobs with similarity >= min-score (0..1)")
    parser.add_argument("--resume", required=True, help="Path to resume (Markdown or text)")
    parser.add_argument("--csv-mode", choices=["w", "a"], default="w", help="Write mode for CSV: w=overwrite, a=append")
    args = parser.parse_args()

    print("Reading resume...")
    resume_text = read_file(args.resume)

    print("Fetching jobs...")
    raw_jobs = (fetch_remotive(args.role) + fetch_remoteok(args.role))[: max(1, args.count)]
    print(f"Fetched {len(raw_jobs)} raw jobs.")

    jobs = filter_jobs(raw_jobs, args.location)
    print(f"{len(jobs)} jobs after location filter/dedupe.")

    print("Scoring jobs with TF-IDF similarity...")
    for j in jobs:
        j["score"] = score_job(resume_text, j.get("description", ""))

    jobs = [j for j in sorted(jobs, key=lambda x: x["score"], reverse=True) if j["score"] >= args.min_score]
    jobs = jobs[: max(1, args.top_k)]
    print(f"Selected {len(jobs)} jobs after scoring (min_score={args.min_score}, top_k={args.top_k}).")

    out_dir = pathlib.Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    save_jobs_csv(jobs, out_dir / "job_listings.csv", mode=args.csv_mode)

    agent = make_agent()

    print("Generating tailored summaries & cover letters...")
    summaries: List[str] = []
    for idx, job in enumerate(jobs, start=1):
        print(f"- [{idx}/{len(jobs)}] {job.get('company','?')} — {job.get('title','?')} (score={job['score']:.2f})")
        prompt = make_prompt(resume_text, job)
        resp = agent.run(prompt)
        text = getattr(resp, "content", str(resp)) or ""

        safe_company = re.sub(r"[^A-Za-z0-9_.-]+", "_", (job.get("company", "") or "Company"))[:50]
        safe_score = f"{job['score']:.2f}"
        write_text(out_dir / "cover_letters" / f"{idx:02d}_{safe_score}_{safe_company}.md", text)

        # Flexible heading match (case-insensitive; stops at next '##' or end)
        m = re.search(r"##\s*Tailored.*?Summary\s*(.*?)(?:\r?\n##|\Z)", text, re.I | re.S)
        if m:
            summaries.append(m.group(1).strip())

    # If no tailored summary captured, generate a general one from the resume
    if not summaries:
        print("No 'Tailored Resume Summary' found; generating a general summary from the resume...")
        general_prompt = (
            "Using only the RESUME below, write an ATS-friendly professional summary "
            "(120–160 words) with 3–5 bullet points including measurable impact.\n\n"
            f"RESUME:\n{resume_text}"
        )
        resp2 = agent.run(general_prompt)
        general_text = getattr(resp2, "content", str(resp2)) or ""
        m2 = re.search(r"(?s)(?:^|\n\n)(.*)", general_text)
        summaries.append(m2.group(1).strip() if m2 else general_text.strip())

    consolidated = "# Tailored Resume Summary\n\n" + summaries[0]
    write_text(out_dir / "Tailored_Resume.md", consolidated)

    print(f"Done. See {out_dir}/ for results.")


if __name__ == "__main__":
    main()
