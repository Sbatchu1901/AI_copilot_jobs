AI Job Copilot (OpenAI + TF-IDF)

A command-line assistant that:

fetches remote job postings,

ranks them by similarity to your resume using TF-IDF cosine similarity, and

generates a Tailored Resume Summary and Cover Letter for the top matches with OpenAI.

Outputs are saved to the output/ folder (CSV of jobs + Markdown files per job).

Features

🔎 Sources: Remotive + RemoteOK (public APIs)

📈 Relevance ranking: TF-IDF + cosine similarity

✍️ AI writing: Tailored resume summary + cover letter for top-K jobs

🧹 Robust CSV writing (handles locked files), HTML stripping, deduping

🔐 Environment-based config (.env, never commit keys)
Clone & create environment
git clone https://github.com/Sbatchu1901/AI_copilot_jobs.git
cd AI_copilot_jobs

# optional but recommended
python -m venv .venv
# Windows (PowerShell)
. .\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

Install dependencies
pip install -r requirements.txt
# If not listed in requirements, also:
pip install python-dotenv scikit-learn requests agno
Configure environment

Create a .env file (do not commit it):
# .env
OPENAI_API_KEY=xx-...
# Optional; defaults to gpt-4o-mini
OPENAI_MODEL=gpt-4o-mini
# .env.example (commit this, not .env)
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4o-mini
Run 
python job_copilot.py \
  --role "Data Analyst" \
  --location "Remote" \
  --count 30 \
  --top-k 5 \
  --min-score 0.12 \
  --resume sample_resume.md \
  --csv-mode w
Outputs 
output/
 ├─ job_listings.csv
 ├─ Tailored_Resume.md
 └─ cover_letters/
     ├─ 01_0.34_CompanyA.md
     ├─ 02_0.31_CompanyB.md
     └─ ...
Project Structure
.
├─ job_copilot.py        # main CLI
├─ requirements.txt
├─ sample_resume.md
├─ .gitignore            # includes `.env`
└─ output/               # generated files
License

MIT © 2025 Srujan Batchu
