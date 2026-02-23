"""
Complete Working Resume Parser
Replace your entire resume_parser.py with this file
"""

import re
import PyPDF2
from docx import Document
from typing import Dict, List


class ResumeParser:
    """Parse resumes and extract structured information"""
    
    def __init__(self):
        pass
    
    def parse_resume(self, file_path: str) -> Dict:
        """
        Main parsing function
        
        Args:
            file_path: Path to resume file (.pdf or .docx)
        
        Returns:
            Dictionary with parsed resume data
        """
        # Extract text
        text = self._extract_text(file_path)
        
        # Parse sections
        contact = self._extract_contact(text)
        skills = self._extract_skills(text)  # FIXED VERSION
        experience = self._extract_experience(text)
        education = self._extract_education(text)
        
        # Calculate experience
        total_exp = self._calculate_experience(experience)
        
        return {
            'contact': contact,
            'skills': skills,
            'experience': experience,
            'education': education,
            'total_experience_years': total_exp,
            'raw_text': text
        }
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF or DOCX"""
        if file_path.endswith('.pdf'):
            return self._extract_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self._extract_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format")
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"PDF extraction error: {e}")
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"DOCX extraction error: {e}")
        return text
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """
        FIXED: Extract skills from resume
        Uses multiple strategies to find skills
        """
        skills = {
            'programming_languages': [],
            'ml_ai': [],
            'frameworks': [],
            'cloud_tools': [],
            'databases': [],
            'other': []
        }
        
        # Comprehensive skill database
        skill_database = {
            'programming_languages': [
                'python', 'java', 'javascript', 'c++', 'c#', 'sql',
                'typescript', 'r', 'matlab', 'scala', 'go', 'rust',
                'php', 'ruby', 'swift', 'kotlin', 'numpy', 'pandas',
                'scikit-learn', 'sklearn'
            ],
            'ml_ai': [
                'machine learning', 'deep learning', 'ml', 'dl',
                'natural language processing', 'nlp', 'computer vision',
                'cv', 'cnn', 'rnn', 'lstm', 'gru', 'transformer', 'transformers',
                'bert', 'gpt', 'llm', 'large language model',
                'neural network', 'ai', 'artificial intelligence',
                'data science', 'opencv', 'yolo', 'spacy', 'nltk',
                'hugging face', 'reinforcement learning'
            ],
            'frameworks': [
                'tensorflow', 'pytorch', 'keras', 'flask', 'fastapi',
                'django', 'streamlit', 'gradio', 'react', 'angular',
                'vue', 'node.js', 'express', 'spring', 'springboot',
                'laravel', '.net', 'rails'
            ],
            'cloud_tools': [
                'aws', 'amazon web services', 'azure', 'gcp',
                'google cloud', 'docker', 'kubernetes', 'k8s',
                'git', 'github', 'gitlab', 'jenkins', 'ci/cd',
                'terraform', 'ansible', 'lambda', 'ec2', 's3',
                'sagemaker'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra',
                'dynamodb', 'sqlite', 'oracle', 'sql server', 'nosql',
                'elasticsearch', 'firebase'
            ]
        }
        
        text_lower = text.lower()
        
        # Search for each skill
        for category, skill_list in skill_database.items():
            for skill in skill_list:
                # Create regex pattern with word boundaries
                # This prevents matching "python" in "pythonic"
                pattern = r'\b' + re.escape(skill) + r'\b'
                
                if re.search(pattern, text_lower):
                    # Format skill name nicely
                    if skill in ['nlp', 'ml', 'dl', 'ai', 'cv', 'sql', 'aws', 'gcp']:
                        formatted = skill.upper()
                    elif skill in ['scikit-learn', 'hugging face', 'node.js']:
                        formatted = skill
                    else:
                        formatted = skill.title()
                    
                    # Avoid duplicates
                    if formatted not in skills[category]:
                        skills[category].append(formatted)
        
        # Sort skills alphabetically in each category
        for category in skills:
            skills[category].sort()
        
        return skills
    
    def _extract_contact(self, text: str) -> Dict:
        """Extract contact information"""
        contact = {
            'name': '',
            'email': '',
            'phone': '',
            'linkedin': '',
            'github': ''
        }
        
        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            contact['email'] = email_match.group()
        
        # Phone (Indian format)
        phone_match = re.search(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', text)
        if phone_match:
            contact['phone'] = phone_match.group().strip()
        
        # LinkedIn
        linkedin_match = re.search(r'linkedin\.com/in/([\w-]+)', text.lower())
        if linkedin_match:
            contact['linkedin'] = f"linkedin.com/in/{linkedin_match.group(1)}"
        
        # GitHub
        github_match = re.search(r'github\.com/([\w-]+)', text.lower())
        if github_match:
            contact['github'] = f"github.com/{github_match.group(1)}"
        
        # Name (first non-empty line that looks like a name)
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 50:
                words = line.split()
                if 2 <= len(words) <= 4 and not any(char in line for char in ['@', 'http', '.']):
                    contact['name'] = line
                    break
        
        return contact
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience (simplified)"""
        experience = []
        
        # Simple extraction - look for company and title patterns
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Look for job title indicators
            title_keywords = ['engineer', 'developer', 'analyst', 'manager', 
                            'scientist', 'consultant', 'architect', 'lead']
            
            if any(keyword in line_lower for keyword in title_keywords):
                # Extract job info
                job = {
                    'title': line.strip(),
                    'company': '',
                    'duration': '',
                    'description': []
                }
                
                # Look for company in next few lines
                for j in range(i+1, min(i+3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and '|' in next_line:
                        parts = next_line.split('|')
                        if len(parts) >= 2:
                            job['company'] = parts[0].strip()
                            job['duration'] = parts[1].strip()
                        break
                
                if job['company'] or job['duration']:
                    experience.append(job)
        
        return experience
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education"""
        education = []
        
        # Look for degree keywords
        degree_keywords = ['bachelor', 'master', 'phd', 'b.tech', 'm.tech', 
                          'b.e', 'm.e', 'bca', 'mca', 'mba', 'b.sc', 'm.sc']
        
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            if any(degree in line_lower for degree in degree_keywords):
                edu = {
                    'degree': line.strip(),
                    'institution': '',
                    'year': ''
                }
                
                # Extract year (4 digits)
                year_match = re.search(r'\b(19|20)\d{2}\b', line)
                if year_match:
                    edu['year'] = year_match.group()
                
                education.append(edu)
        
        return education
    
    def _calculate_experience(self, experience: List[Dict]) -> float:
        """Calculate total years of experience"""
        if not experience:
            return 0.0
        
        # Simple calculation based on number of jobs
        # In real implementation, parse dates and calculate
        return len(experience) * 2.0  # Assume 2 years per job


# Test function
def test_parser():
    """Test the parser"""
    parser = ResumeParser()
    
    # Test with your resume
    result = parser.parse_resume("ArunavJha(1).pdf")
    
    print("=" * 60)
    print("RESUME PARSING RESULTS")
    print("=" * 60)
    
    print(f"\nName: {result['contact']['name']}")
    print(f"Email: {result['contact']['email']}")
    print(f"Phone: {result['contact']['phone']}")
    
    print("\nSKILLS:")
    total_skills = 0
    for category, skills in result['skills'].items():
        if skills:
            print(f"  {category}: {', '.join(skills)}")
            total_skills += len(skills)
    
    print(f"\nTotal Skills: {total_skills}")
    print(f"Experience: {result['total_experience_years']} years")
    
    return result


if __name__ == "__main__":
    test_parser()