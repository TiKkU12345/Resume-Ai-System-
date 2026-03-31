"""
Question Generator - AI-Powered Follow-up Questions
Powered by Claude API (Anthropic) — replaces OpenAI
"""

import os
import json
from typing import List, Dict
import anthropic
from dotenv import load_dotenv

load_dotenv()


def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set in environment variables")
    return anthropic.Anthropic(api_key=api_key)


def _call_claude(system: str, user: str, max_tokens: int = 1000) -> str:
    client = _get_client()
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


class QuestionGenerator:
    """
    Generates intelligent follow-up questions using Claude Sonnet.
    Drop-in replacement for the previous OpenAI-based generator.
    """

    SYSTEM_PROMPT = """You are an expert technical recruiter.
Generate targeted follow-up questions to clarify a candidate's fit for a role.
Return ONLY valid JSON — no markdown fences, no explanation.

Output format:
[
  {
    "question": "The actual question",
    "gap_addressed": "Which gap this addresses",
    "priority": "high|medium|low"
  }
]"""

    def generate_questions(
        self,
        job_data: Dict,
        candidate_data: Dict,
        critical_gaps: List[str],
        missing_info: List[str],
        confidence_score: float,
    ) -> List[Dict[str, str]]:
        """
        Generate context-aware follow-up questions using Claude.

        Args:
            job_data: Parsed job description dict.
            candidate_data: Parsed resume dict.
            critical_gaps: List of critical gap strings from AgentBrain.
            missing_info: List of missing info strings from AgentBrain.
            confidence_score: Current confidence float (0.0–1.0).

        Returns:
            List of question dicts with keys: question, gap_addressed, priority.
        """
        all_skills = []
        for skills in candidate_data.get("skills", {}).values():
            if isinstance(skills, list):
                all_skills.extend(skills)

        user_prompt = f"""Job Title: {job_data.get('title', 'Not specified')}
Required Skills: {', '.join(job_data.get('required_skills', [])[:10])}
Minimum Experience: {job_data.get('min_experience', 0)} years

Candidate Skills: {', '.join(all_skills[:10])}
Number of Experience Entries: {len(candidate_data.get('experience', []))}

Critical Gaps: {', '.join(critical_gaps) if critical_gaps else 'None'}
Missing Info: {', '.join(missing_info) if missing_info else 'None'}
Current Confidence: {confidence_score:.2f}

Generate 2-4 targeted, open-ended follow-up questions.
Each must address a specific gap. Avoid yes/no questions."""

        try:
            raw = _call_claude(self.SYSTEM_PROMPT, user_prompt)
            questions = json.loads(raw)
            if not isinstance(questions, list):
                raise ValueError("Response is not a list")
            return questions
        except json.JSONDecodeError:
            return self._fallback_questions(critical_gaps, missing_info)
        except Exception as e:
            print(f"QuestionGenerator error: {e}")
            return self._fallback_questions(critical_gaps, missing_info)

    def _fallback_questions(
        self,
        critical_gaps: List[str],
        missing_info: List[str],
    ) -> List[Dict[str, str]]:
        """Rule-based fallback if Claude call fails."""
        questions = []
        for gap in critical_gaps[:3]:
            if "experience" in gap.lower():
                questions.append({
                    "question": "Could you describe your work experience in detail — company, role, duration, and key responsibilities?",
                    "gap_addressed": gap,
                    "priority": "high",
                })
            elif "project" in gap.lower():
                questions.append({
                    "question": "Can you walk me through 1–2 relevant projects, including the tech stack and your specific contributions?",
                    "gap_addressed": gap,
                    "priority": "high",
                })
            else:
                questions.append({
                    "question": f"The role requires {gap}. Can you describe a project where you used it?",
                    "gap_addressed": gap,
                    "priority": "high",
                })
        return questions


class AnswerEvaluator:
    """
    Evaluates candidate responses to follow-up questions using Claude.
    Drop-in replacement for the previous OpenAI-based evaluator.
    """

    SYSTEM_PROMPT = """You are an expert technical interviewer evaluating a candidate's answer.
Return ONLY valid JSON — no markdown, no explanation.

Output format:
{
  "satisfactory": true or false,
  "confidence_boost": float between -0.2 and 0.3,
  "reasoning": "brief explanation",
  "follow_up_needed": true or false
}

Scoring guide:
- Specific examples with measurable impact → +0.2 to +0.3
- Relevant but vague experience → +0.1 to +0.2
- Weak or unsupported claims → -0.1 to 0
- Irrelevant answer → -0.2
- No answer or "I don't know" → -0.2"""

    def evaluate_answer(
        self,
        question: str,
        answer: str,
        gap_addressed: str,
        job_data: Dict,
    ) -> Dict:
        """
        Evaluate how well a candidate's answer addresses a gap.

        Args:
            question: The original follow-up question.
            answer: Candidate's response.
            gap_addressed: Which gap this question targets.
            job_data: Parsed JD dict for context.

        Returns:
            Dict with satisfactory, confidence_boost, reasoning, follow_up_needed.
        """
        user_prompt = f"""Question asked: {question}
Gap being addressed: {gap_addressed}
Job title: {job_data.get('title', 'Not specified')}
Required skills: {', '.join(job_data.get('required_skills', [])[:8])}

Candidate's answer:
{answer}

Evaluate this answer."""

        try:
            raw = _call_claude(self.SYSTEM_PROMPT, user_prompt, max_tokens=400)
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "satisfactory": False,
                "confidence_boost": 0.0,
                "reasoning": "Could not evaluate answer.",
                "follow_up_needed": True,
            }
        except Exception as e:
            print(f"AnswerEvaluator error: {e}")
            return {
                "satisfactory": False,
                "confidence_boost": 0.0,
                "reasoning": str(e),
                "follow_up_needed": True,
            }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing QuestionGenerator with Claude...")

    job_data = {
        "title": "Backend Developer",
        "required_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        "min_experience": 3,
    }
    candidate_data = {
        "skills": {"programming": ["Python", "Flask"], "databases": ["MySQL"]},
        "experience": [{"title": "Developer", "company": "XYZ", "duration": "1 year"}],
    }

    try:
        gen = QuestionGenerator()
        questions = gen.generate_questions(
            job_data, candidate_data,
            critical_gaps=["FastAPI", "Docker"],
            missing_info=["No container experience"],
            confidence_score=0.55,
        )
        print(json.dumps(questions, indent=2))
    except Exception as e:
        print(f"Test failed: {e}")
