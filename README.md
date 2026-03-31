<div align="center">

# 🎯 AI Resume Shortlisting System

### Intelligent Resume Screening & Candidate Ranking — Powered by Claude AI

[![Python](https://img.shields.io/badge/Python-3.11.8-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Claude API](https://img.shields.io/badge/Claude_API-Anthropic-6B4FBB?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![spaCy](https://img.shields.io/badge/spaCy-NLP-09A3D5?style=for-the-badge&logo=spacy&logoColor=white)](https://spacy.io)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Live-brightgreen?style=for-the-badge)]()

<br/>

> **Automates resume screening using NLP + LLMs — reducing manual effort by ~80% and eliminating keyword-based bias in hiring pipelines.**

</div>

---

## 📌 Problem Statement

Traditional hiring pipelines are:
- ⏳ **Slow** — Manual review of 100s of resumes per role
- 🎲 **Inconsistent** — Human bias affects shortlisting quality
- 🔍 **Shallow** — Keyword matching misses context and relevance

This system replaces that workflow with an **AI-native pipeline** that semantically understands resumes and job descriptions — not just keyword frequency.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📄 Resume Parsing | Supports PDF & DOCX formats with text extraction |
| 🧠 Semantic Matching | Sentence Transformers compute embedding-based similarity |
| 🤖 LLM Analysis | Claude API extracts skills, experience, and fit rationale |
| 📊 Candidate Ranking | Scored and ranked automatically by relevance |
| 🔐 Admin Workflow | Manual approval gate before final shortlisting |
| 🗄️ Centralized DB | Supabase stores resumes, scores, and metadata securely |
| ⚡ Real-time UI | Interactive Streamlit dashboard with live filtering |

---

## 🧠 System Architecture

```mermaid
graph TB
    subgraph INPUT["📥 Input Layer"]
        A[👤 Recruiter] -->|Uploads resumes| B[PDF / DOCX Parser]
        A -->|Provides Job Description| C[JD Text Input]
    end

    subgraph NLP["🔬 NLP Processing"]
        B --> D[spaCy — Entity Extraction\nSkills · Experience · Education]
        C --> E[Sentence Transformers\nEmbedding Generation]
        D --> E
        E --> F[Cosine Similarity Score]
    end

    subgraph AI["🤖 AI Layer — Claude API"]
        F --> G[Claude — Resume Analysis\nFit Rationale · Red Flags · Highlights]
        G --> H[Structured JSON Output\nScore · Summary · Recommendation]
    end

    subgraph STORAGE["🗄️ Storage — Supabase"]
        H --> I[(Candidates Table)]
        H --> J[(Scores Table)]
        B --> K[(Resume Files)]
    end

    subgraph UI["🖥️ Streamlit Dashboard"]
        I --> L[Ranked Candidate List]
        J --> L
        L --> M[Admin Review Panel]
        M -->|Approve / Reject| N[📧 Shortlisted Pool]
    end

    style INPUT fill:#1e3a5f,color:#fff
    style NLP fill:#2d1b4e,color:#fff
    style AI fill:#4a1b2e,color:#fff
    style STORAGE fill:#1b3a2d,color:#fff
    style UI fill:#3a2d1b,color:#fff
```

---

## 🔄 Data Flow

```mermaid
sequenceDiagram
    participant R as 👤 Recruiter
    participant UI as 🖥️ Streamlit UI
    participant NLP as 🔬 NLP Engine
    participant LLM as 🤖 Claude API
    participant DB as 🗄️ Supabase

    R->>UI: Upload resumes + Job Description
    UI->>NLP: Send raw resume text
    NLP->>NLP: Extract entities (spaCy)
    NLP->>NLP: Generate embeddings (Sentence Transformers)
    NLP->>LLM: Send resume + JD for deep analysis
    LLM-->>NLP: Return score, rationale, highlights
    NLP->>DB: Store candidate profile + score
    DB-->>UI: Fetch ranked candidates
    UI-->>R: Display ranked shortlist
    R->>UI: Approve / Reject candidates
    UI->>DB: Update status in candidates table
```

---

## 🛠️ Tech Stack

```mermaid
graph LR
    subgraph Frontend
        A[🖥️ Streamlit]
    end
    subgraph AI_NLP["AI / NLP"]
        B[🤖 Claude API — Anthropic]
        C[📐 Sentence Transformers]
        D[🔬 spaCy]
    end
    subgraph Backend
        E[🐍 Python 3.11.8]
        F[📄 PyPDF2 / python-docx]
    end
    subgraph Database
        G[🗄️ Supabase — PostgreSQL]
    end

    A --> E
    E --> B
    E --> C
    E --> D
    E --> F
    E --> G
```

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Streamlit | Dashboard, file upload, admin UI |
| **LLM** | Claude API (Anthropic) | Resume analysis, fit rationale, scoring |
| **NLP** | spaCy + Sentence Transformers | Entity extraction + semantic embeddings |
| **Backend** | Python 3.11.8 | Core processing pipeline |
| **File Handling** | PyPDF2, python-docx | Resume text extraction |
| **Database** | Supabase (PostgreSQL) | Candidate storage, scores, auth |

---

## 📂 Project Structure

```
resume-ai-system/
│
├── app.py                  # Main Streamlit application entry point
├── requirements.txt        # Python dependencies
│
├── components/
│   ├── parser.py           # PDF / DOCX text extraction
│   ├── matcher.py          # Embedding generation + cosine similarity
│   ├── llm_analyzer.py     # Claude API integration
│   └── admin.py            # Admin approval workflow
│
├── database/
│   ├── supabase_client.py  # DB connection + queries
│   └── schema.sql          # Table definitions
│
└── utils/
    └── config.py           # Environment variables, constants
```

---

## ⚙️ Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/TiKkU12345/resume-ai-system
cd resume-ai-system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
cp .env.example .env
# Add: ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY

# 4. Run
streamlit run app.py
```

---

## 🔐 Environment Variables

```env
ANTHROPIC_API_KEY=your_claude_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

---

## 📊 Pipeline Performance (Approximate)

| Metric | Value |
|---|---|
| Avg. screening time per resume | ~3–5 seconds |
| Manual effort reduction | ~80% |
| Supported file formats | PDF, DOCX |
| Max batch size tested | 50 resumes |

---

## 🧑‍💻 Built By

**Arunav Kumar (Tikku)**
[GitHub](https://github.com/TiKkU12345) · [Email](mailto:arunav.jr.0604@gmail.com)

---

<div align="center">

*Built for placement portfolio — demonstrating end-to-end AI/ML system design with real-world utility.*

</div>
