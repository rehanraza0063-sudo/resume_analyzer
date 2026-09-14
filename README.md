# ResumeAI — AI Resume Analyzer

A full-stack web application that analyzes resumes, estimates ATS
compatibility, finds skill gaps against a target job role, compares a
resume against a job description, and generates a personalized
improvement roadmap — all running locally with a rule-based analysis
engine (no paid AI API required).

---

## 1. Features

- Upload a resume as **PDF or DOCX**, or paste resume text directly
- Automatic **section detection** (experience, education, skills, projects, summary)
- **ATS-style compatibility score** with a plain-language explanation for every check
- **Skill detection** against a curated technical-skill dictionary
- **Skill-gap analysis** against 8 target roles (Data Analyst, Data Scientist, AI/ML Engineer, Software Engineer, Cloud Engineer, Biomedical Engineer, Business Analyst, Product Analyst)
- **Job description matcher** — paste a JD and get keyword/skill/experience/education match scores
- **Bullet point improver** — rule-based rewrite of weak resume bullets
- **Resume quality checklist** with a completeness percentage
- **Career roadmap** generated from your missing skills
- **Demo mode** — try the whole app instantly with a sample resume
- Fully responsive UI with a mobile navigation menu
- Friendly error handling for corrupted files, empty resumes, and unsupported formats

---

## 2. Tech Stack

**Frontend:** React 18 + Vite (JavaScript, no TypeScript), React Router, Recharts, lucide-react icons
**Backend:** Python 3 + Flask, Flask-CORS
**Database:** SQLite (stores a lightweight history of past analyses)
**Parsing libraries:** pdfplumber (PDF), python-docx (DOCX)

---

## 3. Project Structure

```
resume-analyzer/
│
├── frontend/
│   ├── src/
│   │   ├── components/       # Navbar, Footer, UploadBox, ScoreRing, charts, etc.
│   │   ├── pages/             # Home, Analyze, Dashboard, JobMatch, SkillGap, About
│   │   ├── context/           # ResumeContext (shared analysis state)
│   │   ├── styles/global.css  # design tokens + base styles
│   │   ├── api.js             # fetch wrappers for the Flask backend
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js         # dev proxy: /api -> http://localhost:5000
│   └── package.json
│
├── backend/
│   ├── app.py                 # Flask app + all API routes
│   ├── analyzer.py            # rule-based scoring, skill detection, job matching
│   ├── resume_parser.py       # PDF/DOCX text extraction + section splitting
│   ├── job_roles.py           # job-role -> required-skills database
│   ├── database.py            # SQLite persistence
│   ├── config.py              # optional AI provider config (disabled by default)
│   └── requirements.txt
│
├── sample_data/
│   └── demo_resume.txt        # the resume used by "Try Demo"
│
├── .gitignore
└── README.md
```

---

## 4. Installation & Running Locally (Windows, macOS, Linux)

You need **Python 3.9+** and **Node.js 18+** installed.

### Backend (Flask API — runs on port 5000)

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

The API will start at `http://localhost:5000`. It creates
`resume_analyzer.db` automatically on first run.

### Frontend (React + Vite — runs on port 5173)

Open a **second terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. The Vite dev server
proxies all `/api/*` requests to the Flask backend automatically, so
both servers need to be running at the same time.

---

## 5. How the Application Works

1. The user uploads a PDF/DOCX or pastes resume text on the **Analyze
   Resume** page.
2. If a file was uploaded, it's sent to `POST /api/upload-resume`,
   where `resume_parser.py` extracts raw text with `pdfplumber` or
   `python-docx`.
3. The extracted (or pasted) text is sent to `POST /api/analyze-resume`.
   `analyzer.py` splits the text into sections, detects technical
   skills via keyword matching, and computes five weighted category
   scores (ATS Compatibility, Content Quality, Skills, Formatting,
   Keyword Optimization) that roll up into an overall score.
4. The result is stored in `resume_analyzer.db` and rendered on the
   **Dashboard**: score ring, category bars, resume summary, skills
   found/missing, ATS checklist with explanations, prioritized
   recommendations, a career roadmap, and the bullet-point improver.
5. The **Skill Gap** page lets the user pick a different target role
   at any time and re-queries `POST /api/skill-gap`.
6. The **Job Match** page sends the resume text plus a pasted job
   description to `POST /api/job-match`, which scores keyword,
   skill, experience, and education overlap.
7. **Try Demo** calls `GET /api/demo`, which runs the exact same
   analysis pipeline against a built-in sample resume — no upload
   needed.

All analysis is rule-based and runs entirely on your machine. See
`backend/config.py` for how an external AI provider could be wired in
later without changing the API contract.

---

## 6. Error Handling

The backend returns friendly JSON errors (with proper HTTP status
codes) for: no file uploaded, unsupported file type, oversized files,
corrupted/unreadable PDFs or DOCX files, empty or too-short resumes,
and incomplete job descriptions. The frontend surfaces these as toast
notifications instead of crashing.

---

## 7. Limitations

This is an **educational ATS-style estimate**, not a guarantee of
real ATS or recruiter outcomes. Skill detection relies on keyword
matching, so unconventional phrasing may be missed. Real applicant
tracking systems vary widely between companies and are not fully
reproducible outside of them.

---

## 8. Future Improvements

- Plug in a real LLM (via `AI_PROVIDER` / `AI_API_KEY` in `config.py`) for deeper, more nuanced feedback
- Resume version history and side-by-side comparison over time
- Export the dashboard as a shareable PDF report
- User accounts so analyses persist across devices
- Support for LinkedIn profile import
- Broaden the skill dictionary and job-role database, or make it user-editable
- Multi-language resume support

---

Built as a portfolio project demonstrating a full-stack React + Flask
application with real file parsing, rule-based NLP, and data
visualization.
