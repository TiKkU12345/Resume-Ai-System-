<div align="center">

# 🎯 AI Resume Shortlisting System || [live](https://aisystemusingnlp.streamlit.app/)

### Intelligent Resume Screening & Candidate Ranking — Powered by Claude AI + NLP

[![Python](https://img.shields.io/badge/Python-3.11.8-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Claude API](https://img.shields.io/badge/Claude_Sonnet-Anthropic-6B4FBB?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![spaCy](https://img.shields.io/badge/spaCy-NLP-09A3D5?style=for-the-badge&logo=spacy&logoColor=white)](https://spacy.io)
[![sklearn](https://img.shields.io/badge/scikit--learn-TF--IDF-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Live-brightgreen?style=for-the-badge)]()

<br/>

> **Hybrid AI pipeline: Claude Sonnet handles semantic understanding (resume parsing, JD analysis, fit rationale, interview Q generation) while TF-IDF + spaCy handle fast keyword-level scoring — combined into a ranked shortlist with explainable decisions.**

</div>

---

## 📌 Problem Statement

Traditional hiring pipelines are:
- ⏳ **Slow** — Manual review of 100s of resumes per role
- 🎲 **Inconsistent** — Human bias affects shortlisting quality
- 🔍 **Shallow** — Keyword matching misses context and relevance
- ❓ **Unexplainable** — No rationale for why a candidate was rejected

This system replaces that workflow with a **hybrid AI pipeline** — fast NLP scoring + deep LLM reasoning — with every decision backed by an explainable rationale.

---

## ✨ Key Features

| Feature | Powered By |
|---|---|
| 📄 Resume Parsing — PDF & DOCX | PyPDF2 + python-docx + **Claude Sonnet** |
| 🧠 Semantic Resume Analysis | **Claude Sonnet** (skills, experience, education extraction) |
| 📋 JD Parsing | **Claude Sonnet** (required skills, seniority, must-haves) |
| 📊 Candidate Scoring & Ranking | TF-IDF + Cosine Similarity (sklearn) + spaCy NLP |
| 🤖 Fit Rationale | **Claude Sonnet** (strengths, concerns, recommendation) |
| ❓ Interview Question Generation | **Claude Sonnet** (technical + behavioral + clarification Qs) |
| 🔐 Admin Approval Workflow | Rule-based AgentBrain (confidence thresholds) |
| 🗄️ Centralized Database | Supabase (PostgreSQL) |
| 📈 Analytics Dashboard | Plotly (score distribution, skill gaps, decision breakdown) |

---

## 🧠 System Architecture

```mermaid
graph TB
    subgraph INPUT["📥 Input Layer"]
        A[👤 Recruiter] -->|Uploads PDF/DOCX resumes| B[File Parser\nPyPDF2 · python-docx]
        A -->|Provides Job Description| C[Raw JD Text]
    end

    subgraph CLAUDE["🤖 Claude Sonnet — LLM Layer"]
        B --> D[Resume Analysis\nExtract skills · experience · education]
        C --> E[JD Parsing\nRequired skills · seniority · must-haves]
        D --> F[Fit Rationale\nStrengths · Concerns · Verdict]
        D --> G[Interview Questions\nTechnical · Behavioral · Clarification]
    end

    subgraph NLP["🔬 Fast NLP Scoring — sklearn + spaCy"]
        D --> H[TF-IDF Vectorizer\nResume vs JD text similarity]
        E --> H
        H --> I[Cosine Similarity Score\nOverall · Skills · Exp · Education]
    end

    subgraph AGENT["⚙️ Rule-Based AgentBrain"]
        I --> J{Confidence Threshold}
        F --> J
        J -->|85%+| K[Auto Shortlist]
        J -->|50-84%| L[Ask Questions]
        J -->|below 50%| M[Auto Reject]
    end

    subgraph STORAGE["🗄️ Supabase"]
        K --> N[(Candidates Table)]
        L --> N
        M --> N
        G --> O[(Questions Table)]
    end

    subgraph UI["🖥️ Streamlit Dashboard"]
        N --> P[Ranked Candidate List]
        O --> P
        P --> Q[Admin Review Panel]
        Q -->|Approve / Reject| R[Final Shortlist]
    end

    style CLAUDE fill:#2d1b4e,color:#fff
    style NLP fill:#1b2d4e,color:#fff
    style AGENT fill:#1b4e2d,color:#fff
    style INPUT fill:#1e3a5f,color:#fff
    style STORAGE fill:#3a1b1b,color:#fff
    style UI fill:#3a2d1b,color:#fff
```

---

## 🔄 Request Flow

```mermaid
sequenceDiagram
    participant R as Recruiter
    participant UI as Streamlit
    participant NLP as spaCy + TF-IDF
    participant LLM as Claude Sonnet
    participant DB as Supabase

    R->>UI: Upload resumes + Job Description
    UI->>LLM: Resume text via analyze_resume()
    LLM-->>UI: Structured JSON — skills, exp, education
    UI->>LLM: JD text via parse_job_description()
    LLM-->>UI: Structured requirements JSON
    UI->>NLP: TF-IDF scoring (resume vs JD)
    NLP-->>UI: Overall, Skills, Exp, Edu scores
    UI->>LLM: Profile + Scores via generate_fit_rationale()
    LLM-->>UI: Verdict + Strengths + Concerns + Recommendation
    UI->>LLM: Profile + Gaps via generate_interview_questions()
    LLM-->>UI: Technical + Behavioral + Clarification Qs
    UI->>DB: Store candidate + scores + rationale + questions
    DB-->>UI: Ranked shortlist
    R->>UI: Review and Approve or Reject
```

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
|---|---|---|
| **LLM** | Claude Sonnet (Anthropic) | Resume parsing, JD analysis, fit rationale, interview Qs |
| **NLP / Scoring** | spaCy + TF-IDF (sklearn) | Keyword extraction, cosine similarity scoring |
| **Frontend** | Streamlit | Dashboard, file upload, admin UI, analytics |
| **Decision Engine** | Rule-based AgentBrain | Confidence thresholds → shortlist / question / reject |
| **File Handling** | PyPDF2, python-docx | Extract text from PDF and DOCX resumes |
| **Database** | Supabase (PostgreSQL) | Candidates, scores, questions, auth |
| **Analytics** | Plotly | Score histograms, skill gap charts, decision pie |

---

## 📂 Project Structure

```
resume-ai-system/
│
├── app.py                    # Streamlit entry point + UI pages
├── claude_integration.py     # Claude API module — all 4 LLM features
├── job_resume_matcher.py     # TF-IDF scoring + spaCy NLP
├── agent_brain.py            # Rule-based decision engine
├── resume_parser.py          # PDF / DOCX text extraction
├── authentication.py         # Supabase auth
├── database.py               # Supabase CRUD operations
├── interview_questions.py    # Interview Q UI component
├── bulk_upload.py            # Batch resume upload
├── ats_resume_validator.py   # ATS validation + feedback
├── email_integration.py      # Email notifications
├── generate_question.py      # Q generation + answer evaluation
├── resources.py              # Cached resource loading
└── requirements.txt
```

---

## ⚙️ Local Setup

```bash
# 1. Clone
git clone https://github.com/TiKkU12345/Resume-Ai-System
cd resume-ai-system

# 2. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Set environment variables
# Create .env or add to Streamlit secrets:
ANTHROPIC_API_KEY=your_claude_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# 4. Run
streamlit run app.py
```

---

## 🔐 Environment Variables

```env
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key
```

---

## 🤖 Claude Integration — `claude_integration.py`

Four functions, each calling `claude-sonnet-4-5`:

| Function | Input | Output |
|---|---|---|
| `analyze_resume(text)` | Raw resume text | Structured JSON: skills, experience, education |
| `parse_job_description(text)` | Raw JD text | Required skills, seniority, must-haves |
| `generate_fit_rationale(profile, jd, scores)` | Candidate + JD + scores | Verdict, strengths, concerns, recommendation |
| `generate_interview_questions(profile, jd, scores)` | Candidate + JD + gaps | Technical + behavioral + clarification Qs |

---

## 📊 Analytics Dashboard (Plotly)

- **Decision distribution** — Auto-shortlist vs Questions vs Reject
- **Score distribution** — Candidate score histogram
- **Confidence vs Match Score** — Scatter by decision type
- **Top matched / missing skills** — Horizontal bar charts
- **Experience vs Score** — Scatter with color gradient

---

## 🧑‍💻 Built By

**Arunav Kumar (Tikku)**
[GitHub](https://github.com/TiKkU12345) · [Email](mailto:arunav.jr.0604@gmail.com)

---

<div align="center">

*Hybrid AI system: Claude Sonnet for semantic reasoning + TF-IDF/spaCy for fast scoring — built for placement portfolio demonstrating real-world LLM integration.*

</div>
