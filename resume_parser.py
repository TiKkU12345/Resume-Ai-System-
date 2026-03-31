"""
Resume Parser — with Claude AI Integration
Claude handles semantic extraction; regex/PyPDF2 handle file reading.
"""

import re
import os
import json
import PyPDF2
from docx import Document
from typing import Dict, List


# ── Claude helper (lazy import to avoid crash if key not set at import time) ──
def _claude_parse_resume(text: str) -> Dict:
    """
    Use Claude Sonnet to extract structured data from raw resume text.
    Falls back to None if Claude call fails so regex parser takes over.
    """
    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        client = anthropic.Anthropic(api_key=api_key)
        system = """You are an expert resume parser.
Extract structured information from the resume text and return ONLY valid JSON.
No markdown fences, no explanation — pure JSON only.

Output schema:
{
  "name": "string",
  "email": "string or null",
  "phone": "string or null",
  "linkedin": "string or null",
  "github": "string or null",
  "skills": {
    "programming_languages": [],
    "ml_ai": [],
    "frameworks": [],
    "cloud_tools": [],
    "databases": [],
    "other": []
  },
  "total_experience_years": number,
  "experience": [
    {
      "title": "string",
      "company": "string",
      "duration": "string",
      "description": ["key responsibilities or achievements"]
    }
  ],
  "education": [
    {
      "degree": "string",
      "institution": "string",
      "year": "string or null"
    }
  ],
  "certifications": [],
  "summary": "2-3 sentence professional summary"
}"""

        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1800,
            system=system,
            messages=[{"role": "user", "content": f"Parse this resume:\n\n{text}"}],
        )
        raw = message.content[0].text
        parsed = json.loads(raw)

        # Normalise to match existing app expectations
        # app.py reads resume['contact']['name'] etc.
        result = {
            "contact": {
                "name": parsed.get("name", ""),
                "email": parsed.get("email", ""),
                "phone": parsed.get("phone", ""),
                "linkedin": parsed.get("linkedin", ""),
                "github": parsed.get("github", ""),
            },
            "skills": parsed.get("skills", {}),
            "experience": parsed.get("experience", []),
            "education": parsed.get("education", []),
            "certifications": parsed.get("certifications", []),
            "total_experience_years": parsed.get("total_experience_years", 0),
            "summary": parsed.get("summary", ""),
            "raw_text": text,
            "_parsed_by": "claude",
        }
        return result

    except Exception as e:
        print(f"[ResumeParser] Claude parse failed, falling back to regex: {e}")
        return None


class ResumeParser:
    """
    Parse resumes and extract structured information.
    Strategy: Claude Sonnet first → regex fallback if Claude unavailable/fails.
    """

    def __init__(self):
        pass

    def parse_resume(self, file_path: str) -> Dict:
        """
        Main parsing function.

        Args:
            file_path: Path to resume file (.pdf or .docx)

        Returns:
            Dictionary with parsed resume data compatible with existing app.py
        """
        text = self._extract_text(file_path)

        # Try Claude first
        claude_result = _claude_parse_resume(text)
        if claude_result:
            return claude_result

        # Fallback: original regex-based parsing
        contact = self._extract_contact(text)
        skills = self._extract_skills(text)
        experience = self._extract_experience(text)
        education = self._extract_education(text)
        total_exp = self._calculate_experience(experience)

        return {
            "contact": contact,
            "skills": skills,
            "experience": experience,
            "education": education,
            "total_experience_years": total_exp,
            "raw_text": text,
            "_parsed_by": "regex",
        }

    # ── File extraction ───────────────────────────────────────────────────────

    def _extract_text(self, file_path: str) -> str:
        if file_path.endswith(".pdf"):
            return self._extract_from_pdf(file_path)
        elif file_path.endswith(".docx"):
            return self._extract_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format — use PDF or DOCX")

    def _extract_from_pdf(self, file_path: str) -> str:
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"PDF extraction error: {e}")
        return text

    def _extract_from_docx(self, file_path: str) -> str:
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"DOCX extraction error: {e}")
        return text

    # ── Regex fallback parsers (unchanged from original) ─────────────────────

    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        skills = {
            "programming_languages": [],
            "ml_ai": [],
            "frameworks": [],
            "cloud_tools": [],
            "databases": [],
            "other": [],
        }

        skill_database = {
            "programming_languages": [
                "python", "java", "javascript", "c++", "c#", "sql",
                "typescript", "r", "matlab", "scala", "go", "rust",
                "php", "ruby", "swift", "kotlin", "numpy", "pandas",
                "scikit-learn", "sklearn",
            ],
            "ml_ai": [
                "machine learning", "deep learning", "ml", "dl",
                "natural language processing", "nlp", "computer vision",
                "cv", "cnn", "rnn", "lstm", "gru", "transformer", "transformers",
                "bert", "gpt", "llm", "large language model",
                "neural network", "ai", "artificial intelligence",
                "data science", "opencv", "yolo", "spacy", "nltk",
                "hugging face", "reinforcement learning",
            ],
            "frameworks": [
                "tensorflow", "pytorch", "keras", "flask", "fastapi",
                "django", "streamlit", "gradio", "react", "angular",
                "vue", "node.js", "express", "spring", "springboot",
                "laravel", ".net", "rails",
            ],
            "cloud_tools": [
                "aws", "amazon web services", "azure", "gcp",
                "google cloud", "docker", "kubernetes", "k8s",
                "git", "github", "gitlab", "jenkins", "ci/cd",
                "terraform", "ansible", "lambda", "ec2", "s3", "sagemaker",
            ],
            "databases": [
                "mysql", "postgresql", "mongodb", "redis", "cassandra",
                "dynamodb", "sqlite", "oracle", "sql server", "nosql",
                "elasticsearch", "firebase",
            ],
        }

        text_lower = text.lower()
        for category, skill_list in skill_database.items():
            for skill in skill_list:
                pattern = r"\b" + re.escape(skill) + r"\b"
                if re.search(pattern, text_lower):
                    if skill in ["nlp", "ml", "dl", "ai", "cv", "sql", "aws", "gcp"]:
                        formatted = skill.upper()
                    elif skill in ["scikit-learn", "hugging face", "node.js"]:
                        formatted = skill
                    else:
                        formatted = skill.title()
                    if formatted not in skills[category]:
                        skills[category].append(formatted)

        for category in skills:
            skills[category].sort()

        return skills

    def _extract_contact(self, text: str) -> Dict:
        contact = {"name": "", "email": "", "phone": "", "linkedin": "", "github": ""}

        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        if email_match:
            contact["email"] = email_match.group()

        phone_match = re.search(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]", text)
        if phone_match:
            contact["phone"] = phone_match.group().strip()

        linkedin_match = re.search(r"linkedin\.com/in/([\w-]+)", text.lower())
        if linkedin_match:
            contact["linkedin"] = f"linkedin.com/in/{linkedin_match.group(1)}"

        github_match = re.search(r"github\.com/([\w-]+)", text.lower())
        if github_match:
            contact["github"] = f"github.com/{github_match.group(1)}"

        lines = text.split("\n")
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 50:
                words = line.split()
                if 2 <= len(words) <= 4 and not any(
                    char in line for char in ["@", "http", "."]
                ):
                    contact["name"] = line
                    break

        return contact

    def _extract_experience(self, text: str) -> List[Dict]:
        experience = []
        lines = text.split("\n")
        title_keywords = [
            "engineer", "developer", "analyst", "manager",
            "scientist", "consultant", "architect", "lead",
        ]

        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in title_keywords):
                job = {"title": line.strip(), "company": "", "duration": "", "description": []}
                for j in range(i + 1, min(i + 3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and "|" in next_line:
                        parts = next_line.split("|")
                        if len(parts) >= 2:
                            job["company"] = parts[0].strip()
                            job["duration"] = parts[1].strip()
                        break
                if job["company"] or job["duration"]:
                    experience.append(job)

        return experience

    def _extract_education(self, text: str) -> List[Dict]:
        education = []
        degree_keywords = [
            "bachelor", "master", "phd", "b.tech", "m.tech",
            "b.e", "m.e", "bca", "mca", "mba", "b.sc", "m.sc",
        ]
        lines = text.split("\n")

        for line in lines:
            if any(deg in line.lower() for deg in degree_keywords):
                edu = {"degree": line.strip(), "institution": "", "year": ""}
                year_match = re.search(r"\b(19|20)\d{2}\b", line)
                if year_match:
                    edu["year"] = year_match.group()
                education.append(edu)

        return education

    def _calculate_experience(self, experience: List[Dict]) -> float:
        return len(experience) * 2.0


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = ResumeParser()
    result = parser.parse_resume("ArunavJha(1).pdf")
    print(f"Parsed by: {result.get('_parsed_by', 'unknown')}")
    print(f"Name: {result['contact']['name']}")
    print(f"Email: {result['contact']['email']}")
    total = sum(len(v) for v in result["skills"].values() if isinstance(v, list))
    print(f"Total skills found: {total}")
