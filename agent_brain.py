"""
Agent Brain - AI-powered candidate decision making
Makes intelligent hiring decisions based on multiple factors
"""

from enum import Enum
from typing import Dict, List, Any


class AgentDecision(Enum):
    """Possible agent decisions"""
    AUTO_SHORTLIST = "auto_shortlist"
    ASK_QUESTIONS = "ask_questions"
    AUTO_REJECT = "auto_reject"


class ConfidenceLevel(Enum):
    """Confidence levels for decisions"""
    VERY_HIGH = "very_high"  # 0.85+
    HIGH = "high"            # 0.70-0.84
    MEDIUM = "medium"        # 0.50-0.69
    LOW = "low"              # 0.30-0.49
    VERY_LOW = "very_low"    # <0.30


class AgentBrain:
    """
    AI Agent that makes intelligent hiring decisions
    """
    
    def __init__(self, job_data: Dict):
        """
        Initialize agent with job requirements
        
        Args:
            job_data: Parsed job description data
        """
        self.job_data = job_data
        self.required_skills = set([s.lower() for s in job_data.get('required_skills', [])])
        self.preferred_skills = set([s.lower() for s in job_data.get('preferred_skills', [])])
        self.min_experience = job_data.get('min_experience', 0)
    
    def analyze_candidate(self, resume: Dict, scores: Dict) -> Dict:
        """
        Perform comprehensive candidate analysis
        
        Args:
            resume: Parsed resume data
            scores: Calculated matching scores
        
        Returns:
            dict: Complete agent analysis with decision
        """
        # Extract candidate skills
        candidate_skills = set()
        for skill_category in resume.get('skills', {}).values():
            if isinstance(skill_category, list):
                candidate_skills.update([s.lower() for s in skill_category])
        
        # Get candidate experience
        candidate_exp = resume.get('total_experience_years', 0)
        
        # Identify gaps
        critical_gaps = self._identify_critical_gaps(
            candidate_skills, 
            candidate_exp, 
            scores
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            scores, 
            candidate_skills, 
            candidate_exp,
            critical_gaps
        )
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(confidence)
        
        # Make decision
        decision = self._make_decision(
            confidence_level, 
            critical_gaps, 
            scores['overall']
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            decision, 
            confidence, 
            scores, 
            critical_gaps,
            candidate_exp
        )
        
        # Identify missing information
        missing_info = self._identify_missing_info(resume)
        
        return {
            'decision': decision,
            'confidence': round(confidence, 2),
            'confidence_level': confidence_level,
            'reasoning': reasoning,
            'critical_gaps': critical_gaps,
            'missing_info': missing_info
        }
    
    def _identify_critical_gaps(
        self, 
        candidate_skills: set, 
        candidate_exp: float,
        scores: Dict
    ) -> List[str]:
        """Identify critical gaps that could disqualify candidate"""
        gaps = []
        
        # Missing required skills
        missing_required = self.required_skills - candidate_skills
        if missing_required:
            for skill in list(missing_required)[:3]:  # Top 3
                gaps.append(f"Missing required skill: {skill}")
        
        # Experience gap
        if self.min_experience > 0 and candidate_exp < self.min_experience * 0.7:
            gap_years = self.min_experience - candidate_exp
            gaps.append(f"Experience gap: {gap_years:.1f} years below requirement")
        
        # Low skill match
        if scores.get('skills', 0) < 40:
            gaps.append("Very low technical skill alignment")
        
        return gaps
    
    def _calculate_confidence(
        self,
        scores: Dict,
        candidate_skills: set,
        candidate_exp: float,
        critical_gaps: List[str]
    ) -> float:
        """
        Calculate confidence score (0.0 to 1.0)
        
        Factors:
        - Overall match score (40%)
        - Skill coverage (30%)
        - Experience match (20%)
        - Gap penalty (10%)
        """
        # Base confidence from overall score
        score_confidence = scores['overall'] / 100.0
        
        # Skill coverage confidence
        total_job_skills = len(self.required_skills) + len(self.preferred_skills)
        if total_job_skills > 0:
            matched_count = len(candidate_skills.intersection(
                self.required_skills.union(self.preferred_skills)
            ))
            skill_confidence = matched_count / total_job_skills
        else:
            skill_confidence = 0.5
        
        # Experience confidence
        if self.min_experience > 0:
            exp_ratio = candidate_exp / self.min_experience
            exp_confidence = min(1.0, exp_ratio)
        else:
            exp_confidence = 0.8
        
        # Gap penalty
        gap_penalty = len(critical_gaps) * 0.1
        
        # Weighted confidence
        confidence = (
            score_confidence * 0.40 +
            skill_confidence * 0.30 +
            exp_confidence * 0.20 +
            (1.0 - gap_penalty) * 0.10
        )
        
        return max(0.0, min(1.0, confidence))
    
    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Map confidence score to level"""
        if confidence >= 0.85:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.70:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.50:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.30:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _make_decision(
        self,
        confidence_level: ConfidenceLevel,
        critical_gaps: List[str],
        overall_score: float
    ) -> AgentDecision:
        """
        Make hiring decision based on analysis
        
        Decision Logic:
        - VERY_HIGH confidence (85%+) → AUTO_SHORTLIST
        - HIGH confidence (70-84%) + no critical gaps → AUTO_SHORTLIST
        - HIGH confidence with gaps → ASK_QUESTIONS
        - MEDIUM confidence (50-69%) → ASK_QUESTIONS
        - LOW/VERY_LOW confidence (<50%) → AUTO_REJECT
        """
        if confidence_level == ConfidenceLevel.VERY_HIGH:
            return AgentDecision.AUTO_SHORTLIST
        
        elif confidence_level == ConfidenceLevel.HIGH:
            if len(critical_gaps) == 0:
                return AgentDecision.AUTO_SHORTLIST
            else:
                return AgentDecision.ASK_QUESTIONS
        
        elif confidence_level == ConfidenceLevel.MEDIUM:
            return AgentDecision.ASK_QUESTIONS
        
        else:  # LOW or VERY_LOW
            return AgentDecision.AUTO_REJECT
    
    def _generate_reasoning(
        self,
        decision: AgentDecision,
        confidence: float,
        scores: Dict,
        critical_gaps: List[str],
        candidate_exp: float
    ) -> List[str]:
        """Generate human-readable reasoning for the decision"""
        reasoning = []
        
        # Overall assessment
        if decision == AgentDecision.AUTO_SHORTLIST:
            reasoning.append(f"Strong match with {confidence*100:.0f}% confidence")
            reasoning.append(f"Overall score: {scores['overall']:.1f}%")
            
        elif decision == AgentDecision.ASK_QUESTIONS:
            reasoning.append(f"Promising candidate but needs clarification ({confidence*100:.0f}% confidence)")
            
            if critical_gaps:
                reasoning.append(f"Has {len(critical_gaps)} areas needing discussion")
                
        else:  # AUTO_REJECT
            reasoning.append(f"Below hiring threshold ({confidence*100:.0f}% confidence)")
            
            if critical_gaps:
                reasoning.append(f"Multiple critical gaps identified ({len(critical_gaps)} issues)")
        
        # Specific strengths
        if scores.get('skills', 0) >= 80:
            reasoning.append("✓ Strong technical skills alignment")
        
        if candidate_exp >= self.min_experience * 1.2:
            reasoning.append("✓ Exceeds experience requirements")
        
        # Specific weaknesses
        if scores.get('skills', 0) < 50:
            reasoning.append("✗ Significant skill gaps")
        
        if candidate_exp < self.min_experience * 0.7:
            reasoning.append("✗ Below required experience level")
        
        return reasoning
    
    def _identify_missing_info(self, resume: Dict) -> List[str]:
        """Identify missing or unclear information in resume"""
        missing = []
        
        # Check contact info
        contact = resume.get('contact', {})
        if not contact.get('email'):
            missing.append("Email address not found")
        if not contact.get('phone'):
            missing.append("Phone number not found")
        
        # Check experience details
        if not resume.get('experience') or len(resume.get('experience', [])) == 0:
            missing.append("No work experience listed")
        
        # Check education
        if not resume.get('education') or len(resume.get('education', [])) == 0:
            missing.append("No education details found")
        
        # Check skills
        skills = resume.get('skills', {})
        total_skills = sum(len(v) for v in skills.values() if isinstance(v, list))
        if total_skills < 3:
            missing.append("Very few skills listed")
        
        return missing