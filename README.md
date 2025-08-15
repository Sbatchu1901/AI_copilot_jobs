---
# AI Copilot Jobs (OpenAI + TF-IDF + Agentic AI)

A command-line assistant that:
1. Fetches remote job postings (Remotive + RemoteOK)
2. Ranks them against your resume using **TF-IDF cosine similarity**
3. Generates a **Tailored Resume Summary** and **Cover Letter** with OpenAI using an **Agentic AI architecture**

All results are saved to the `output/` folder (CSV + Markdown letters).

---

## ✨ Features

* 🔎 **Job Sources**: Remotive & RemoteOK APIs
* 📈 **Relevance Scoring**: TF-IDF + cosine similarity
* 🤖 **Agentic AI**: Autonomous reasoning to follow ATS-friendly rules
* ✍️ **Generative AI**: Creates contextually relevant summaries & cover letters
* 🧹 CSV writer that survives locked files (Excel open)
* 🧯 Deduping, location filtering, HTML stripping
* 🔐 Env-driven config (`.env`) — **never commit secrets**

---

## 🤖 How Agentic AI & Generative AI are Used

This project is more than a prompt → answer.
It combines **Agentic AI** for process control with **Generative AI** for content creation.

### 1. Agentic AI Workflow

The `agno.Agent`:

* Maintains **stateful context** (fixed instructions)
* **Extracts** must-have skills from job descriptions
* **Maps** resume achievements to job requirements with metrics
* **Enforces** output structure:

  * Section 1: Tailored Resume Summary (ATS-optimized)
  * Section 2: Company-specific Cover Letter

### 2. Generative AI Layer

The `OpenAIChat` model:

* **Synthesizes** new text using your resume + job post
* **Adapts tone & keywords** to match ATS systems and hiring expectations
* Avoids fabricated details through system constraints

### 3. Why This Matters

* **Manual process**: Slow, inconsistent
* **Pure LLM**: Unreliable structure, style drift
* **Agentic + Generative combo**: Consistent structure + natural, tailored writing at scale

---

## 🚀 Quickstart

### 1) Clone & set up Python

```bash
git clone https://github.com/Sbatchu1901/AI_copilot_jobs.git
cd AI_copilot_jobs

python -m venv .venv
. .\.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate      # mac/Linux
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure `.env` (never commit it)

```ini
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Commit a safe `.env.example` instead:

```ini
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4o-mini
```

### 4) Run

```bash
python job_copilot.py \
  --role "Data Analyst" \
  --location "Remote" \
  --count 30 \
  --top-k 5 \
  --min-score 0.12 \
  --resume sample_resume.md \
  --csv-mode w
```

---

## ⚙️ CLI Options

| Flag          | Required | Default | Description                                    |
| ------------- | -------: | ------- | ---------------------------------------------- |
| `--role`      |        ✅ | –       | Target role (e.g., `"Data Analyst"`)           |
| `--location`  |          | `""`    | Filter across title/company/location           |
| `--count`     |          | `20`    | Max jobs to fetch before scoring               |
| `--top-k`     |          | `5`     | Number of top jobs to generate letters for     |
| `--min-score` |          | `0.12`  | Min similarity score to keep                   |
| `--resume`    |        ✅ | –       | Path to resume file                            |
| `--csv-mode`  |          | `w`     | `w` overwrite, `a` append to job\_listings.csv |

---

## 📂 Project Structure

```
.
├─ job_copilot.py        # Main CLI script
├─ requirements.txt      # Python dependencies
├─ sample_resume.md      # Example resume
├─ .gitignore            # Must include `.env`
├─ .env.example          # Template for environment variables
└─ output/               # Generated files
   ├─ job_listings.csv
   ├─ Tailored_Resume.md
   └─ cover_letters/
       ├─ 01_0.34_CompanyA.md
       ├─ 02_0.31_CompanyB.md
```

---

## 🛡️ Git Hygiene

Add to `.gitignore`:

```
.env
.env.*
*.pem
*.key
*.secret
```

Optional pre-commit guard:

```bash
mkdir -p .git/hooks
cat > .git/hooks/pre-commit <<'SH'
#!/usr/bin/env bash
if git diff --cached --name-only | grep -E '(^|/)\.env($|\.|/)' >/dev/null; then
  echo "❌ Refusing to commit .env. Use .env.example instead."; exit 1
fi
if git diff --cached | grep -E '(OPENAI_API_KEY|sk-[A-Za-z0-9_-]{20,})' >/dev/null; then
  echo "❌ Possible secret detected in staged changes."; exit 1
fi
exit 0
SH
chmod +x .git/hooks/pre-commit
```

---

## 🛠 Troubleshooting

* **Repository not found** → Fix remote:

```bash
git remote set-url origin https://github.com/Sbatchu1901/AI_copilot_jobs.git
```

* **CSV locked by Excel** → Script writes to a timestamped fallback
* **No jobs returned** → Broaden `--role` or clear `--location`
* **OpenAI errors** → Check `OPENAI_API_KEY` and quotas

---

## 📜 License

MIT © 2025 Srujan Batchu

---
