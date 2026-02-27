"""
AI Job-Resume Matcher & Ranking Engine - Step 2
Intelligently matches resumes with job descriptions and ranks candidates
"""

import json
import re
import os
import sys
import subprocess
from typing import Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from collections import Counter


try:
    from agent_brain import AgentBrain
except ImportError:
    # Define a minimal AgentBrain if import fails
    from enum import Enum
    
    class Decision(Enum):
        STRONG_YES = "Strong Yes"
        YES = "Yes"
        MAYBE = "Maybe"
        NO = "No"
    
    class ConfidenceLevel(Enum):
        HIGH = "High"
        MEDIUM = "Medium"
        LOW = "Low"
    
    class AgentAnalysis:
        def __init__(self, decision, confidence_score, confidence_level, reasoning, critical_gaps, missing_info):
            self.decision = decision
            self.confidence_score = confidence_score
            self.confidence_level = confidence_level
            self.reasoning = reasoning
            self.critical_gaps = critical_gaps
            self.missing_info = missing_info
    
    class AgentBrain:
        def __init__(self, job_data):
            self.job_data = job_data
        
        def analyze_candidate(self, resume, scores):
            decision = Decision.YES if scores['overall_score'] >= 70 else Decision.MAYBE
            confidence = min(100, scores['overall_score'] + 10)
            confidence_level = ConfidenceLevel.HIGH if confidence >= 80 else ConfidenceLevel.MEDIUM
            reasoning = f"Based on overall score of {scores['overall_score']:.1f}%"
            critical_gaps = scores.get('missing_skills', [])[:3]
            missing_info = []
            
            return AgentAnalysis(decision, confidence, confidence_level, reasoning, critical_gaps, missing_info)


# Load spaCy model with auto-download
def load_spacy_model():
    """Load spaCy model, download if not found"""
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        print("📥 Downloading spaCy model en_core_web_sm...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        return spacy.load("en_core_web_sm")

nlp = spacy.load("en_core_web_sm")


class JobDescriptionParser:
    """Parse and extract key information from job descriptions"""
    
    def __init__(self):
        self.experience_patterns = [
            r'(\d+)\+?\s*(?:to|\-)?\s*(\d+)?\s*(?:years?|yrs?)',
            r'(\d+)\+\s*(?:years?|yrs?)',
        ]
        
        self.education_levels = {
            'phd': 5, 'ph.d': 5, 'doctorate': 5,
            'masters': 4, 'master': 4, 'm.tech': 4, 'm.sc': 4, 'mba': 4,
            'bachelors': 3, 'bachelor': 3, 'b.tech': 3, 'b.sc': 3, 'b.e': 3,
            'diploma': 2,
            'high school': 1
        }
    
    def parse_job_description(self, job_text: str) -> Dict:
        """
        Parse job description and extract structured information
        
        Args:
            job_text: Raw job description text
            
        Returns:
            Dictionary with parsed job requirements
        """
        job_data = {
            'raw_text': job_text,
            'title': '',
            'required_skills': [],
            'preferred_skills': [],
            'min_experience': 0,
            'max_experience': None,
            'education_required': '',
            'responsibilities': [],
            'keywords': [],
            'must_have_skills': [],
            'nice_to_have_skills': []
        }
        
        # Extract job title (usually first line or contains "position", "role")
        job_data['title'] = self._extract_job_title(job_text)
        
        # Extract experience requirements
        job_data['min_experience'], job_data['max_experience'] = self._extract_experience(job_text)
        
        # Extract skills
        job_data['required_skills'], job_data['preferred_skills'] = self._extract_skills(job_text)
        
        # Extract must-have vs nice-to-have
        job_data['must_have_skills'] = self._extract_must_have_skills(job_text)
        job_data['nice_to_have_skills'] = self._extract_nice_to_have_skills(job_text)
        
        # Extract education requirements
        job_data['education_required'] = self._extract_education(job_text)
        
        # Extract keywords using NLP
        job_data['keywords'] = self._extract_keywords(job_text)
        
        return job_data
    
    def _extract_job_title(self, text: str) -> str:
        """Extract job title from description"""
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line) < 100:
                # Check for job title indicators
                if any(keyword in line.lower() for keyword in ['position', 'role', 'job title', 'hiring for']):
                    return line
                # First substantial line might be title
                if len(line.split()) <= 10 and len(line) > 10:
                    return line
        
        return "Position Not Specified"
    
    def _extract_experience(self, text: str) -> Tuple[int, int]:
        """Extract minimum and maximum experience requirements"""
        text_lower = text.lower()
        
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                match = matches[0]
                if isinstance(match, tuple):
                    min_exp = int(match[0]) if match[0] else 0
                    max_exp = int(match[1]) if len(match) > 1 and match[1] else None
                    return min_exp, max_exp
                else:
                    return int(match), None
        
        # Check for "fresher" or "entry level"
        if any(term in text_lower for term in ['fresher', 'entry level', '0 years', 'no experience']):
            return 0, 2
        
        return 0, None

    def _calculate_skills_score(
        self, 
        resume_data: Dict, 
        job_data: Dict
    ) ->Tuple[float, List[str], List[str]]:
        """ULTRA AGGRESSIVE skill matching"""

        # Get ALL text from resume
        full_text = ""

        # Add everything
        for exp in resume_data.get('experience', []):
            full_text += " " + str(exp)
        for proj in resume_data.get('projects', []):
            full_text += " " + str(proj)
        for edu in resume_data.get('education', []):
            full_text += " " + str(edu)
        for cat, skills in resume_data.get('skills', {}).items():
            full_text += " " + " ".join(skills)

        full_text_lower = full_text.lower()

        # Job skills
        required = [s.lower() for s in job_data.get('required_skills', [])]
        preferred = [s.lower() for s in job_data.get('preferred_skills', [])]
        all_skills = required + preferred

        matched = []
        missing = []

        # Super simple matching
        for skill in all_skills:
            if skill in full_text_lower:
                matched.append(skill)
            else:
                missing.append(skill)

        # Score
        if all_skills:
            score = (len(matched) / len(all_skills)) * 100
        else:
            score = 100

        return score, matched, missing
    
    def _extract_skills(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract required and preferred skills"""
        required_skills = []
        preferred_skills = []
        
        # Common skills database (you can expand this)
        all_skills = [
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'Go', 'Rust', 'PHP',
            'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'Spring',
            'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Cassandra',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'CI/CD',
            'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'NLP',
            'Git', 'Agile', 'Scrum', 'REST API', 'GraphQL', 'Microservices',
            'HTML', 'CSS', 'TypeScript', 'Swift', 'Kotlin', 'Scala'
        ]
        
        text_lower = text.lower()
        
        for skill in all_skills:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                # Determine if required or preferred
                # Look for context around the skill
                skill_index = text_lower.find(skill.lower())
                context = text_lower[max(0, skill_index-100):min(len(text_lower), skill_index+100)]
                
                if any(term in context for term in ['required', 'must have', 'mandatory', 'essential']):
                    required_skills.append(skill)
                elif any(term in context for term in ['preferred', 'nice to have', 'plus', 'bonus']):
                    preferred_skills.append(skill)
                else:
                    required_skills.append(skill)  # Default to required
        
        return required_skills, preferred_skills
    
    def _extract_must_have_skills(self, text: str) -> List[str]:
        """Extract must-have skills"""
        must_have = []
        text_lower = text.lower()
        
        # Look for sections with must-have indicators
        must_have_section = re.search(
            r'(?:must have|required|essential|mandatory)[\s\S]{0,500}',
            text_lower
        )
        
        if must_have_section:
            section_text = must_have_section.group()
            # Extract skills from this section
            skills = self._extract_skills(section_text)[0]
            must_have.extend(skills)
        
        return list(set(must_have))
    
    def _extract_nice_to_have_skills(self, text: str) -> List[str]:
        """Extract nice-to-have skills"""
        nice_to_have = []
        text_lower = text.lower()
        
        # Look for sections with nice-to-have indicators
        nice_section = re.search(
            r'(?:nice to have|preferred|plus|bonus|optional)[\s\S]{0,500}',
            text_lower
        )
        
        if nice_section:
            section_text = nice_section.group()
            skills = self._extract_skills(section_text)[1]
            nice_to_have.extend(skills)
        
        return list(set(nice_to_have))
    
    def _extract_education(self, text: str) -> str:
        """Extract education requirements"""
        text_lower = text.lower()
        
        highest_level = ''
        highest_score = 0
        
        for edu, score in self.education_levels.items():
            if edu in text_lower and score > highest_score:
                highest_level = edu
                highest_score = score
        
        return highest_level.title() if highest_level else 'Not Specified'
    
    def _extract_keywords(self, text: str, top_n=20) -> List[str]:
        """Extract important keywords using NLP"""
        doc = nlp(text.lower())
        
        # Extract nouns and proper nouns
        keywords = []
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop and len(token.text) > 2:
                keywords.append(token.text)
        
        # Count frequency
        keyword_freq = Counter(keywords)
        
        # Return top keywords
        return [word for word, _ in keyword_freq.most_common(top_n)]


class JobResumeMatcher:
    """Match resumes with job descriptions using multiple algorithms"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english'
        )
    
    # def calculate_match_score(
    #     self, 
    #     resume_data: Dict, 
    #     job_data: Dict
    # ) -> Dict:
    #     """
    #     Calculate comprehensive match score between resume and job
        
    #     Returns:
    #         Dictionary with overall score and breakdown
    #     """
    #     scores = {
    #         'overall_score': 0,
    #         'skills_score': 0,
    #         'experience_score': 0,
    #         'education_score': 0,
    #         'keywords_score': 0,
    #         'semantic_score': 0,
    #         'matched_skills': [],
    #         'missing_skills': [],
    #         'experience_gap': 0,
    #         'explanation': {}
    #     }
        
    #     # 1. Skills Matching (40% weight)
    #     scores['skills_score'], scores['matched_skills'], scores['missing_skills'] = \
    #         self._calculate_skills_score(resume_data, job_data)
        
    #     # 2. Experience Matching (30% weight)
    #     scores['experience_score'], scores['experience_gap'] = \
    #         self._calculate_experience_score(resume_data, job_data)
        
    #     # 3. Education Matching (15% weight)
    #     scores['education_score'] = self._calculate_education_score(resume_data, job_data)
        
    #     # 4. Keywords Matching (10% weight)
    #     scores['keywords_score'] = self._calculate_keywords_score(resume_data, job_data)
        
    #     # 5. Semantic Similarity (5% weight)
    #     scores['semantic_score'] = self._calculate_semantic_score(resume_data, job_data)
        
    #     # Calculate overall score
    #     scores['overall_score'] = (
    #         scores['skills_score'] * 0.40 +
    #         scores['experience_score'] * 0.30 +
    #         scores['education_score'] * 0.15 +
    #         scores['keywords_score'] * 0.10 +
    #         scores['semantic_score'] * 0.05
    #     )
        
    #     # Generate explanation
    #     scores['explanation'] = self._generate_explanation(scores, resume_data, job_data)
        
    #     return scores
    
    def _calculate_skills_score(self, resume_data, job_data):
        """
        Calculate skills match score with proper type handling
        
        Args:
            resume_data: Parsed resume data
            job_data: Parsed job description data
        
        Returns:
            tuple: (score, matched_skills, missing_skills, gap_explanation)
        """
        try:
            # Extract skills from resume - handle different formats
            resume_skills = []
            skills_dict = resume_data.get('skills', {})
            
            if isinstance(skills_dict, dict):
                for skill_category, skill_list in skills_dict.items():
                    if isinstance(skill_list, list):
                        resume_skills.extend(skill_list)
                    elif isinstance(skill_list, str):
                        resume_skills.append(skill_list)
            elif isinstance(skills_dict, list):
                resume_skills = skills_dict
            
            # Normalize skills (lowercase, strip whitespace)
            resume_skills = [str(s).lower().strip() for s in resume_skills if s]
            
            # Extract required and preferred skills from job
            required_skills = job_data.get('required_skills', [])
            preferred_skills = job_data.get('preferred_skills', [])
            
            # Ensure they're lists
            if not isinstance(required_skills, list):
                required_skills = [required_skills] if required_skills else []
            if not isinstance(preferred_skills, list):
                preferred_skills = [preferred_skills] if preferred_skills else []
            
            # Normalize job skills
            required_skills = [str(s).lower().strip() for s in required_skills if s]
            preferred_skills = [str(s).lower().strip() for s in preferred_skills if s]
            
            # Find matches
            matched_required = []
            matched_preferred = []
            
            for req_skill in required_skills:
                if any(req_skill in resume_skill or resume_skill in req_skill 
                       for resume_skill in resume_skills):
                    matched_required.append(req_skill)
            
            for pref_skill in preferred_skills:
                if any(pref_skill in resume_skill or resume_skill in pref_skill 
                       for resume_skill in resume_skills):
                    matched_preferred.append(pref_skill)
            
            # Calculate score
            total_required = len(required_skills) if required_skills else 1
            total_preferred = len(preferred_skills) if preferred_skills else 1
            
            required_score = (len(matched_required) / total_required) * 100
            preferred_score = (len(matched_preferred) / total_preferred) * 100
            
            # Weighted average: 70% required, 30% preferred
            final_score = (required_score * 0.7) + (preferred_score * 0.3)
            
            # Find missing skills
            missing_required = [s for s in required_skills if s not in matched_required]
            missing_preferred = [s for s in preferred_skills if s not in matched_preferred]
            
            # Combine matched and missing
            all_matched = matched_required + matched_preferred
            all_missing = missing_required + missing_preferred
            
            # Create gap explanation
            gap_explanation = ""
            if missing_required:
                gap_explanation += f"Missing {len(missing_required)} required skills: {', '.join(missing_required[:3])}"
            if missing_preferred:
                if gap_explanation:
                    gap_explanation += "; "
                gap_explanation += f"Missing {len(missing_preferred)} preferred skills"
            
            return (
                round(final_score, 2),
                all_matched[:20],  # Limit to top 20
                all_missing[:20],
                gap_explanation or "No significant skill gaps"
            )
            
        except Exception as e:
            print(f"Error calculating skills score: {e}")
            import traceback
            traceback.print_exc()
            
            # Return safe defaults
            return (0.0, [], [], f"Error calculating skills: {str(e)}")
    
    
    def _calculate_experience_score(self, resume_data, job_data):
        """
        Calculate experience score with proper type handling
        
        Args:
            resume_data: Parsed resume data
            job_data: Parsed job description data
        
        Returns:
            tuple: (score, gap_explanation)
        """
        try:
            # Get candidate's total experience
            total_experience = resume_data.get('total_experience_years', 0)
            
            # Ensure it's a number
            try:
                total_experience = float(total_experience)
            except (ValueError, TypeError):
                total_experience = 0.0
            
            # Get required experience
            min_experience = job_data.get('min_experience', 0)
            
            # Ensure it's a number
            try:
                min_experience = float(min_experience)
            except (ValueError, TypeError):
                min_experience = 0.0
            
            # Calculate score
            if min_experience == 0:
                score = 100.0  # No experience required
            elif total_experience >= min_experience:
                # Has required experience or more
                score = min(100.0, 80.0 + (total_experience - min_experience) * 5)
            else:
                # Less than required
                score = (total_experience / min_experience) * 80.0
            
            # Create gap explanation
            gap = min_experience - total_experience
            if gap > 0:
                gap_explanation = f"Needs {gap:.1f} more years of experience"
            elif gap < -2:
                gap_explanation = f"Has {abs(gap):.1f} years more than required"
            else:
                gap_explanation = "Meets experience requirements"
            
            return (round(score, 2), gap_explanation)
            
        except Exception as e:
            print(f"Error calculating experience score: {e}")
            return (0.0, f"Error: {str(e)}")
    
    
    def _calculate_education_score(self, resume_data, job_data):
        """
        Calculate education score with proper type handling
        
        Args:
            resume_data: Parsed resume data
            job_data: Parsed job description data
        
        Returns:
            tuple: (score, gap_explanation)
        """
        try:
            # Get education from resume
            education = resume_data.get('education', [])
            
            # Ensure it's a list
            if not isinstance(education, list):
                education = [education] if education else []
            
            # Education levels hierarchy
            education_levels = {
                'phd': 5,
                'doctorate': 5,
                'masters': 4,
                'master': 4,
                'mba': 4,
                'bachelors': 3,
                'bachelor': 3,
                'associate': 2,
                'diploma': 1,
                'high school': 1
            }
            
            # Find highest education level
            candidate_level = 0
            highest_degree = "None"
            
            for edu in education:
                if isinstance(edu, dict):
                    degree = str(edu.get('degree', '')).lower()
                elif isinstance(edu, str):
                    degree = edu.lower()
                else:
                    continue
                
                for level_name, level_value in education_levels.items():
                    if level_name in degree:
                        if level_value > candidate_level:
                            candidate_level = level_value
                            highest_degree = degree
            
            # Get required education from job
            required_education = job_data.get('education_level', '').lower()
            required_level = 0
            
            for level_name, level_value in education_levels.items():
                if level_name in required_education:
                    required_level = level_value
                    break
                
            # Calculate score
            if required_level == 0:
                score = 100.0  # No specific education required
            elif candidate_level >= required_level:
                score = 100.0
            elif candidate_level > 0:
                score = (candidate_level / required_level) * 100.0
            else:
                score = 0.0
            
            # Create gap explanation
            if candidate_level >= required_level:
                gap_explanation = "Meets education requirements"
            elif candidate_level == 0:
                gap_explanation = "No formal education listed"
            else:
                gap_explanation = f"Has {highest_degree}, may need higher qualification"
            
            return (round(score, 2), gap_explanation)
            
        except Exception as e:
            print(f"Error calculating education score: {e}")
            return (50.0, "Could not verify education")
    
    
    # Usage in calculate_match_score method:
    def calculate_match_score(self, resume_data, job_data):
        """
        Calculate overall match score with proper error handling
        
        Returns:
            dict: Score breakdown with all components
        """
        try:
            scores = {}
            
            # Calculate individual scores
            (scores['skills_score'], 
             scores['matched_skills'], 
             scores['missing_skills'],
             scores['skills_gap']) = self._calculate_skills_score(resume_data, job_data)
            
            (scores['experience_score'], 
             scores['experience_gap']) = self._calculate_experience_score(resume_data, job_data)
            
            (scores['education_score'], 
             scores['education_gap']) = self._calculate_education_score(resume_data, job_data)
            
            # Calculate overall score (weighted average)
            scores['overall_score'] = (
                scores['skills_score'] * 0.5 +
                scores['experience_score'] * 0.3 +
                scores['education_score'] * 0.2
            )
            
            # Round overall score
            scores['overall_score'] = round(scores['overall_score'], 2)
            
            return scores
            
        except Exception as e:
            print(f"Error in calculate_match_score: {e}")
            import traceback
            traceback.print_exc()
            
            # Return safe defaults
            return {
                'overall_score': 0.0,
                'skills_score': 0.0,
                'experience_score': 0.0,
                'education_score': 0.0,
                'matched_skills': [],
                'missing_skills': [],
                'skills_gap': 'Error calculating score',
                'experience_gap': '',
                'education_gap': ''
            }
    
    def _calculate_keywords_score(
        self, 
        resume_data: Dict, 
        job_data: Dict
    ) -> float:
        """Calculate keyword match score"""
        # Get resume text (combine all text fields)
        resume_text = ' '.join([
            resume_data.get('summary', ''),
            ' '.join([exp.get('description', '') for exp in resume_data.get('experience', [])]),
            ' '.join([proj.get('description', '') for proj in resume_data.get('projects', [])])
        ]).lower()
        
        job_keywords = job_data.get('keywords', [])
        
        if not job_keywords:
            return 100.0
        
        # Count matching keywords
        matched_count = sum(1 for keyword in job_keywords if keyword in resume_text)
        
        score = (matched_count / len(job_keywords)) * 100
        
        return score
    
    def _calculate_semantic_score(
        self, 
        resume_data: Dict, 
        job_data: Dict
    ) -> float:
        """Calculate semantic similarity using TF-IDF"""
        try:
            # Prepare texts
            resume_text = ' '.join([
                resume_data.get('summary', ''),
                ' '.join([exp.get('description', '') for exp in resume_data.get('experience', [])]),
            ])
            
            job_text = job_data.get('raw_text', '')
            
            if not resume_text or not job_text:
                return 50.0
            
            # Calculate TF-IDF similarity
            vectors = self.vectorizer.fit_transform([job_text, resume_text])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            
            # Convert to percentage
            score = similarity * 100
            
            return score
        except:
            return 50.0  # Default score if calculation fails
    
    def _generate_explanation(
        self, 
        scores: Dict, 
        resume_data: Dict, 
        job_data: Dict
    ) -> Dict:
        """Generate human-readable explanation of the match"""
        explanation = {
            'summary': '',
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # Overall assessment
        overall = scores['overall_score']
        if overall >= 80:
            explanation['summary'] = "Excellent match! This candidate meets most requirements."
        elif overall >= 60:
            explanation['summary'] = "Good match. Candidate has relevant skills but may have some gaps."
        elif overall >= 40:
            explanation['summary'] = "Moderate match. Consider if willing to train or if skills are transferable."
        else:
            explanation['summary'] = "Low match. Significant gaps in required qualifications."
        
        # Strengths
        if scores['skills_score'] >= 70:
            explanation['strengths'].append(
                f"Strong skills match ({len(scores['matched_skills'])} matching skills)"
            )
        
        if scores['experience_score'] >= 80:
            exp_years = resume_data.get('total_experience_years', 0)
            explanation['strengths'].append(
                f"Meets experience requirement ({exp_years} years)"
            )
        
        if scores['education_score'] >= 90:
            explanation['strengths'].append("Meets education requirements")
        
        # Weaknesses
        if scores['skills_score'] < 60:
            missing_count = len(scores['missing_skills'])
            explanation['weaknesses'].append(
                f"Missing {missing_count} required skills"
            )
        
        if scores['experience_gap'] > 0:
            explanation['weaknesses'].append(
                f"Needs {scores['experience_gap']} more years of experience"
            )
        
        if scores['education_score'] < 70:
            explanation['weaknesses'].append("May not meet education requirements")
        
        # Recommendations
        if scores['overall_score'] >= 70:
            explanation['recommendations'].append("Recommend for interview")
        elif scores['overall_score'] >= 50:
            explanation['recommendations'].append("Consider for phone screen")
            if scores['missing_skills']:
                explanation['recommendations'].append(
                    f"Assess proficiency in: {', '.join(scores['missing_skills'][:3])}"
                )
        else:
            explanation['recommendations'].append("Consider other candidates first")
        
        return explanation


class CandidateRanker:
    """Enhanced with Agent Decision Logic"""
    
    def __init__(self):
        # Your existing initialization
        pass
    
    def rank_candidates(self, resumes, job_description):
        """
        Rank candidates with AI Agent logic
        
        Args:
            resumes: List of parsed resume data
            job_description: Job description string or parsed job data
        
        Returns:
            List of ranked candidates with agent decisions
        """
        # Parse job description if it's a string
        if isinstance(job_description, str):
            parser = JobDescriptionParser()
            job_data = parser.parse_job_description(job_description)
        else:
            job_data = job_description
        
        # Initialize Agent Brain
        agent = AgentBrain(job_data)
        
        ranked_candidates = []
        
        for resume in resumes:
            # Calculate base scores (your existing logic)
            scores = self._calculate_scores(resume, job_data)
            
            # Get agent analysis
            agent_analysis = agent.analyze_candidate(resume, scores)
            
            # Combine everything
            candidate_result = {
                # Basic info
                'name': resume['contact'].get('name', 'Unknown'),
                'email': resume['contact'].get('email', 'N/A'),
                'phone': resume['contact'].get('phone', 'N/A'),
                
                # Scores
                'overall_score': scores['overall'],
                'skills_score': scores['skills'],
                'experience_score': scores['experience'],
                'education_score': scores['education'],
                
                # Experience
                'total_experience': resume.get('total_experience_years', 0),
                
                # Skills
                'matched_skills': scores.get('matched_skills', []),
                'missing_skills': scores.get('missing_skills', []),
                
                # Agent Decision - THIS IS THE KEY PART
                'agent_decision': agent_analysis['decision'].value,
                'confidence_score': agent_analysis['confidence'],
                'confidence_level': agent_analysis['confidence_level'].value,
                'agent_reasoning': agent_analysis['reasoning'],
                'critical_gaps': agent_analysis['critical_gaps'],
                'missing_info': agent_analysis.get('missing_info', []),
                
                # Store resume data for follow-up questions
                'resume_data': resume,
                
                # Explanation
                'explanation': self._generate_explanation(resume, scores, job_data)
            }
            
            ranked_candidates.append(candidate_result)
        
        # Sort by overall score
        ranked_candidates.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return ranked_candidates
    
    def _calculate_scores(self, resume, job_data):
        """
        Calculate matching scores between resume and job
        
        Returns:
            dict: Scores and matched/missing skills
        """
        # Extract skills from resume
        resume_skills = set()
        for skill_category in resume.get('skills', {}).values():
            if isinstance(skill_category, list):
                resume_skills.update([s.lower() for s in skill_category])
        
        # Extract required skills from job
        required_skills = set([s.lower() for s in job_data.get('required_skills', [])])
        preferred_skills = set([s.lower() for s in job_data.get('preferred_skills', [])])
        all_job_skills = required_skills.union(preferred_skills)
        
        # Calculate skill match
        matched_skills = list(resume_skills.intersection(all_job_skills))
        missing_required = list(required_skills - resume_skills)
        missing_preferred = list(preferred_skills - resume_skills)
        missing_skills = missing_required + missing_preferred
        
        # Skills score (40% weight)
        if required_skills:
            required_match_rate = len(required_skills.intersection(resume_skills)) / len(required_skills)
            preferred_match_rate = len(preferred_skills.intersection(resume_skills)) / len(preferred_skills) if preferred_skills else 0
            skills_score = (required_match_rate * 0.7 + preferred_match_rate * 0.3) * 100
        else:
            skills_score = 50  # Default if no skills specified
        
        # Experience score (35% weight)
        candidate_exp = resume.get('total_experience_years', 0)
        required_exp = job_data.get('min_experience', 0)
        
        if required_exp == 0:
            experience_score = 100
        elif candidate_exp >= required_exp * 1.5:
            experience_score = 100
        elif candidate_exp >= required_exp:
            experience_score = 80 + (candidate_exp - required_exp) * 4
        else:
            experience_score = (candidate_exp / required_exp) * 70
        
        experience_score = min(100, experience_score)
        
        # Education score (25% weight)
        education_score = self._calculate_education_score(resume, job_data)
        
        # Overall score
        overall_score = (
            skills_score * 0.40 +
            experience_score * 0.35 +
            education_score * 0.25
        )
        
        return {
            'overall': round(overall_score, 1),
            'skills': round(skills_score, 1),
            'experience': round(experience_score, 1),
            'education': round(education_score, 1),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'missing_required': missing_required,
            'missing_preferred': missing_preferred
        }
    
    def _calculate_education_score(self, resume, job_data):
        """Calculate education matching score"""
        education = resume.get('education', [])
        
        if not education:
            return 30  # Low score for no education info
        
        # Check for relevant degrees
        degrees = []
        for edu in education:
            degree = edu.get('degree', '').lower()
            degrees.append(degree)
        
        # Scoring logic
        if any('phd' in d or 'doctorate' in d for d in degrees):
            return 100
        elif any('master' in d or 'mba' in d or 'm.tech' in d for d in degrees):
            return 90
        elif any('bachelor' in d or 'b.tech' in d or 'b.e' in d for d in degrees):
            return 80
        else:
            return 60
    
    def _generate_explanation(self, resume, scores, job_data):
        """Generate human-readable explanation"""
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Analyze scores
        if scores['skills'] >= 80:
            strengths.append("Strong technical skill match")
        elif scores['skills'] < 50:
            weaknesses.append("Lacks several required technical skills")
        
        if scores['experience'] >= 80:
            strengths.append("Meets or exceeds experience requirements")
        elif scores['experience'] < 50:
            weaknesses.append("Below required experience level")
        
        if scores['education'] >= 80:
            strengths.append("Strong educational background")
        
        # Missing skills analysis
        missing_required = scores.get('missing_required', [])
        if missing_required:
            weaknesses.append(f"Missing {len(missing_required)} required skills")
        
        # Recommendations
        if scores['overall'] >= 80:
            recommendations.append("Highly recommended for interview")
        elif scores['overall'] >= 60:
            recommendations.append("Good candidate, consider for interview")
        else:
            recommendations.append("May need additional screening")
        
        return {
            'summary': f"Overall match score of {scores['overall']:.1f}%",
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendations': recommendations
        }


    def generate_report(
        self, 
        ranked_candidates: List[Dict],
        job_description: str,
        output_file: str = "ranking_report.txt"
    ):
        """Generate detailed ranking report"""
        report = []
        report.append("=" * 80)
        report.append("CANDIDATE RANKING REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Job summary
        job_data = self.job_parser.parse_job_description(job_description)
        report.append(f"Position: {job_data['title']}")
        report.append(f"Required Experience: {job_data['min_experience']}+ years")
        report.append(f"Key Skills: {', '.join(job_data['required_skills'][:5])}")
        report.append("")
        report.append("=" * 80)
        report.append(f"Total Candidates Evaluated: {len(ranked_candidates)}")
        report.append("=" * 80)
        report.append("")
        
        # Individual candidate details
        for i, candidate in enumerate(ranked_candidates, 1):
            report.append(f"\n{'='*80}")
            report.append(f"RANK #{i}: {candidate['name']}")
            report.append(f"{'='*80}")
            report.append(f"Overall Match Score: {candidate['overall_score']}%")
            report.append(f"Email: {candidate['email']}")
            report.append(f"Phone: {candidate['phone']}")
            report.append(f"Total Experience: {candidate['total_experience']} years")
            report.append("")
            
            # Score breakdown
            report.append("Score Breakdown:")
            report.append(f"  • Skills Match: {candidate['skills_score']}%")
            report.append(f"  • Experience Match: {candidate['experience_score']}%")
            report.append(f"  • Education Match: {candidate['education_score']}%")
            report.append("")
            
            # Matched skills
            if candidate['matched_skills']:
                report.append(f"✓ Matched Skills ({len(candidate['matched_skills'])}): ")
                report.append(f"  {', '.join(candidate['matched_skills'][:10])}")
                report.append("")
            
            # Missing skills
            if candidate['missing_skills']:
                report.append(f"✗ Missing Skills ({len(candidate['missing_skills'])}): ")
                report.append(f"  {', '.join(candidate['missing_skills'][:10])}")
                report.append("")
            
            # Explanation
            exp = candidate['explanation']
            report.append(f"Assessment: {exp['summary']}")
            report.append("")
            
            if exp['strengths']:
                report.append("Strengths:")
                for strength in exp['strengths']:
                    report.append(f"  ✓ {strength}")
                report.append("")
            
            if exp['weaknesses']:
                report.append("Weaknesses:")
                for weakness in exp['weaknesses']:
                    report.append(f"  ✗ {weakness}")
                report.append("")
            
            if exp['recommendations']:
                report.append("Recommendation:")
                for rec in exp['recommendations']:
                    report.append(f"  → {rec}")
        
        # Write to file
        report_text = '\n'.join(report)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return report_text
    

class AgentRanker(CandidateRanker):
    """
    Enhanced ranker with agent decision-making
    Extends your existing CandidateRanker
    """
    
    def __init__(self):
        super().__init__()
        from agent_brain import AgentBrain
        self.agent_brain_class = AgentBrain
    
    def rank_candidates_with_agent(
        self, 
        resumes: List[Dict], 
        job_description: str,
        top_n: int = None
    ) -> List[Dict]:
        """
        Rank candidates WITH agent decision-making
        
        Returns candidates with agent analysis included
        """
        # Parse job description
        job_data = self.job_parser.parse_job_description(job_description)
        
        # Create agent brain
        agent = self.agent_brain_class(job_data)
        
        ranked_candidates = []
        
        for resume in resumes:
            # Calculate match scores (your existing logic)
            scores = self.matcher.calculate_match_score(resume, job_data)
            
            # NEW: Agent analysis
            analysis = agent.analyze_candidate(resume, scores)
            
            # Create enhanced candidate profile
            candidate = {
                'name': resume['contact'].get('name', 'Unknown'),
                'email': resume['contact'].get('email', ''),
                'phone': resume['contact'].get('phone', ''),
                'overall_score': round(scores['overall_score'], 2),
                'skills_score': round(scores['skills_score'], 2),
                'experience_score': round(scores['experience_score'], 2),
                'education_score': round(scores['education_score'], 2),
                'total_experience': resume.get('total_experience_years', 0),
                'matched_skills': scores['matched_skills'],
                'missing_skills': scores['missing_skills'],
                'explanation': scores['explanation'],
                
                # NEW: Agent fields
                'confidence_score': round(analysis.confidence_score, 2),
                'confidence_level': analysis.confidence_level.value,
                'agent_decision': analysis.decision.value,
                'agent_reasoning': analysis.reasoning,
                
                'critical_gaps': analysis.critical_gaps,
                'missing_info': analysis.missing_info,
                
                'resume_data': resume
            }
            
            ranked_candidates.append(candidate)
        
        # Sort by overall score
        ranked_candidates.sort(key=lambda x: x['overall_score'], reverse=True)
        
        if top_n:
            return ranked_candidates[:top_n]
        
        return ranked_candidates
