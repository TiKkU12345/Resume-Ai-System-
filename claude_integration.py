"""
Claude AI Integration Module
Handles all LLM-powered features:
  1. Resume analysis   — extract skills, experience, education
  2. JD parsing        — extract structured requirements from raw JD text
  3. Candidate fit rationale — explain why shortlist/reject
  4. Interview question generation — role-specific questions per candidate
"""

import os
import json
import anthropic
from typing import Dict, List, Optional

# ── Client ────────────────────────────────────────────────────────────────────
def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. Add it to your .env or Streamlit secrets."
        )
    return anthropic.Anthropic(api_key=api_key)


def _call_claude(system: str, user: str, max_tokens: int = 1024) -> str:
    """
    Generic wrapper around Claude claude-sonnet-4-5.
    Returns the text content of the first response block.
    Raises on API errors.
    """
    client = _get_client()
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


# ── 1. Resume Analysis ────────────────────────────────────────────────────────
RESUME_SYSTEM = """You are an expert resume parser.
Given raw resume text, extract structured information and return ONLY valid JSON.
No explanation, no markdown fences — pure JSON only.

Output schema:
{
  "name": "string",
  "email": "string or null",
  "phone": "string or null",
  "skills": {
    "technical": ["list of technical skills"],
    "soft": ["list of soft skills"],
    "tools": ["frameworks, tools, platforms"]
  },
  "total_experience_years": number,
  "experience": [
    {
      "title": "string",
      "company": "string",
      "duration": "string",
      "highlights": ["key achievements / responsibilities"]
    }
  ],
  "education": [
    {
      "degree": "string",
      "institution": "string",
      "year": "string or null"
    }
  ],
  "certifications": ["list or empty array"],
  "summary": "2-3 sentence professional summary"
}"""


def analyze_resume(resume_text: str) -> Dict:
    """
    Parse raw resume text using Claude.

    Args:
        resume_text: Plain text content of the resume.

    Returns:
        Structured dict with name, skills, experience, education, etc.
        Falls back to a minimal error dict if parsing fails.
    """
    user_prompt = f"Parse this resume:\n\n{resume_text}"
    try:
        raw = _call_claude(RESUME_SYSTEM, user_prompt, max_tokens=1500)
        return json.loads(raw)
    except json.JSONDecodeError:
        # Claude returned something non-JSON — extract what we can
        return {
            "name": "Unknown",
            "email": None,
            "phone": None,
            "skills": {"technical": [], "soft": [], "tools": []},
            "total_experience_years": 0,
            "experience": [],
            "education": [],
            "certifications": [],
            "summary": raw[:300] if raw else "Could not parse resume.",
        }
    except Exception as e:
        return {"error": str(e), "name": "Unknown"}


# ── 2. JD Parsing ─────────────────────────────────────────────────────────────
JD_SYSTEM = """You are an expert job description parser.
Extract structured hiring requirements and return ONLY valid JSON. No markdown.

Output schema:
{
  "title": "string",
  "required_skills": ["must-have technical skills"],
  "preferred_skills": ["nice-to-have skills"],
  "must_have_skills": ["non-negotiable requirements"],
  "nice_to_have_skills": ["bonus qualifications"],
  "min_experience": number,
  "max_experience": number or null,
  "education_required": "string e.g. B.Tech / B.E or equivalent",
  "responsibilities": ["key responsibilities"],
  "keywords": ["important domain keywords for matching"],
  "seniority": "junior | mid | senior | lead | not specified"
}"""


def parse_job_description(jd_text: str) -> Dict:
    """
    Extract structured requirements from a raw job description using Claude.

    Args:
        jd_text: Raw job description text.

    Returns:
        Structured dict with required_skills, experience range, etc.
        Falls back to empty structure on failure.
    """
    user_prompt = f"Parse this job description:\n\n{jd_text}"
    try:
        raw = _call_claude(JD_SYSTEM, user_prompt, max_tokens=1024)
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "title": "Unknown Role",
            "required_skills": [],
            "preferred_skills": [],
            "must_have_skills": [],
            "nice_to_have_skills": [],
            "min_experience": 0,
            "max_experience": None,
            "education_required": "",
            "responsibilities": [],
            "keywords": [],
            "seniority": "not specified",
        }
    except Exception as e:
        return {"error": str(e)}


# ── 3. Candidate Fit Rationale ────────────────────────────────────────────────
RATIONALE_SYSTEM = """You are a senior technical recruiter.
Given a candidate's profile, their match scores, and the job requirements,
write a concise hiring rationale.

Return ONLY valid JSON. No markdown.

Output schema:
{
  "overall_verdict": "Strong Hire | Hire | Maybe | Reject",
  "one_line_summary": "One sentence summary for the recruiter dashboard",
  "strengths": ["2-4 specific strengths relevant to this role"],
  "concerns": ["2-4 specific concerns or gaps"],
  "recommendation": "2-3 sentence final recommendation explaining the decision",
  "suggested_interview_focus": ["areas to probe during interview"]
}"""


def generate_fit_rationale(
    candidate_profile: Dict,
    job_data: Dict,
    scores: Dict,
) -> Dict:
    """
    Generate a human-readable hiring rationale for a candidate using Claude.

    Args:
        candidate_profile: Parsed resume dict (from analyze_resume or existing parser).
        job_data: Parsed JD dict.
        scores: Dict with overall_score, skills_score, experience_score, etc.

    Returns:
        Rationale dict with verdict, strengths, concerns, recommendation.
    """
    user_prompt = f"""
Job Title: {job_data.get('title', 'Not specified')}
Required Skills: {', '.join(job_data.get('required_skills', []))}
Min Experience: {job_data.get('min_experience', 0)} years

Candidate Name: {candidate_profile.get('name', 'Unknown')}
Candidate Skills: {json.dumps(candidate_profile.get('skills', {}))}
Candidate Experience: {candidate_profile.get('total_experience_years', 0)} years
Education: {json.dumps(candidate_profile.get('education', []))}

Match Scores:
- Overall: {scores.get('overall_score', scores.get('overall', 0)):.1f}%
- Skills: {scores.get('skills_score', scores.get('skills', 0)):.1f}%
- Experience: {scores.get('experience_score', scores.get('experience', 0)):.1f}%
- Education: {scores.get('education_score', scores.get('education', 0)):.1f}%

Matched Skills: {', '.join(scores.get('matched_skills', []))}
Missing Skills: {', '.join(scores.get('missing_skills', []))}

Generate a hiring rationale for this candidate.
"""
    try:
        raw = _call_claude(RATIONALE_SYSTEM, user_prompt, max_tokens=800)
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "overall_verdict": "Maybe",
            "one_line_summary": "Could not generate rationale.",
            "strengths": [],
            "concerns": [],
            "recommendation": raw[:400] if raw else "No rationale available.",
            "suggested_interview_focus": [],
        }
    except Exception as e:
        return {"error": str(e)}


# ── 4. Interview Question Generation ─────────────────────────────────────────
QUESTION_SYSTEM = """You are an expert technical interviewer.
Generate targeted interview questions for a candidate based on their profile and the role.

Return ONLY valid JSON. No markdown.

Output schema:
{
  "technical_questions": [
    {
      "question": "string",
      "topic": "which skill/area this tests",
      "difficulty": "easy | medium | hard",
      "why_asked": "what gap or strength this probes"
    }
  ],
  "behavioral_questions": [
    {
      "question": "string",
      "competency": "e.g. teamwork, ownership, problem-solving"
    }
  ],
  "clarification_questions": [
    {
      "question": "string",
      "reason": "what missing info this resolves"
    }
  ]
}"""


def generate_interview_questions(
    candidate_profile: Dict,
    job_data: Dict,
    scores: Dict,
    num_technical: int = 4,
    num_behavioral: int = 3,
    num_clarification: int = 2,
) -> Dict:
    """
    Generate role-specific interview questions for a candidate using Claude.

    Args:
        candidate_profile: Parsed resume dict.
        job_data: Parsed JD dict.
        scores: Match scores dict.
        num_technical: How many technical questions to generate.
        num_behavioral: How many behavioral questions.
        num_clarification: How many clarification questions.

    Returns:
        Dict with technical_questions, behavioral_questions, clarification_questions.
    """
    user_prompt = f"""
Job Title: {job_data.get('title', 'Not specified')}
Required Skills: {', '.join(job_data.get('required_skills', []))}

Candidate: {candidate_profile.get('name', 'Unknown')}
Candidate Skills: {json.dumps(candidate_profile.get('skills', {}))}
Experience: {candidate_profile.get('total_experience_years', 0)} years
Missing Skills: {', '.join(scores.get('missing_skills', []))}
Matched Skills: {', '.join(scores.get('matched_skills', []))}
Overall Score: {scores.get('overall_score', scores.get('overall', 0)):.1f}%

Generate:
- {num_technical} technical questions (focus on matched AND missing skills)
- {num_behavioral} behavioral questions (role-relevant competencies)
- {num_clarification} clarification questions (probe gaps or ambiguities in resume)
"""
    try:
        raw = _call_claude(QUESTION_SYSTEM, user_prompt, max_tokens=1200)
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "technical_questions": [],
            "behavioral_questions": [],
            "clarification_questions": [],
            "raw_response": raw[:500] if raw else "",
        }
    except Exception as e:
        return {"error": str(e)}


# ── Convenience: full pipeline for one candidate ──────────────────────────────
def run_full_claude_analysis(
    resume_text: str,
    jd_text: str,
    existing_scores: Optional[Dict] = None,
) -> Dict:
    """
    Run the complete Claude pipeline for a single candidate:
      1. Parse resume
      2. Parse JD
      3. Generate fit rationale  (uses existing_scores if provided, else zeros)
      4. Generate interview questions

    Args:
        resume_text: Raw resume text.
        jd_text: Raw job description text.
        existing_scores: Optional pre-computed scores from TF-IDF matcher.
                         If None, scores default to 0 (rationale still works).

    Returns:
        {
          "resume": {...},
          "job": {...},
          "rationale": {...},
          "questions": {...}
        }
    """
    resume_data = analyze_resume(resume_text)
    job_data = parse_job_description(jd_text)
    scores = existing_scores or {
        "overall_score": 0, "skills_score": 0,
        "experience_score": 0, "education_score": 0,
        "matched_skills": [], "missing_skills": [],
    }
    rationale = generate_fit_rationale(resume_data, job_data, scores)
    questions = generate_interview_questions(resume_data, job_data, scores)

    return {
        "resume": resume_data,
        "job": job_data,
        "rationale": rationale,
        "questions": questions,
    }
