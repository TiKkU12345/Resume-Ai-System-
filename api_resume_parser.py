"""
API-Based Resume Parser
Uses OpenAI GPT for fast, accurate resume parsing
No heavy ML models - Works great on iOS!
"""

import streamlit as st
import json
import re
from typing import Dict, Any, Optional
import PyPDF2
import docx
from io import BytesIO
from app_config import get_secret

# Only if OpenAI API key is available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class APIResumeParser:
    """Fast resume parser using OpenAI API"""
    
    def __init__(self):
        """Initialize parser with API key from secrets"""
        self.api_key = get_secret("OPENAI_API_KEY", None)
        
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)
            self.use_api = True
        else:
            self.use_api = False
            st.warning("⚠️ OpenAI API not configured. Using basic parsing.")
    
    def parse_resume(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse resume from file content
        
        Args:
            file_content: Resume file bytes
            filename: Original filename
        
        Returns:
            Parsed resume data dictionary
        """
        # Extract text from file
        text = self._extract_text(file_content, filename)
        
        if not text or len(text.strip()) < 50:
            return self._get_empty_resume()
        
        # Parse using API or fallback
        if self.use_api:
            return self._parse_with_api(text, filename)
        else:
            return self._parse_basic(text, filename)
    
    def _extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from PDF or DOCX"""
        try:
            if filename.lower().endswith('.pdf'):
                return self._extract_pdf_text(file_content)
            elif filename.lower().endswith('.docx'):
                return self._extract_docx_text(file_content)
            else:
                return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            st.error(f"Error extracting text: {str(e)}")
            return ""
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            st.error(f"PDF extraction error: {str(e)}")
            return ""
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            doc_file = BytesIO(file_content)
            doc = docx.Document(doc_file)
            
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            st.error(f"DOCX extraction error: {str(e)}")
            return ""
    
    def _parse_with_api(self, text: str, filename: str) -> Dict[str, Any]:
        """Parse resume using OpenAI API"""
        try:
            # Create prompt for structured extraction
            prompt = f"""Extract the following information from this resume in JSON format:

{{
  "name": "Full name",
  "email": "Email address",
  "phone": "Phone number",
  "location": "City, State/Country",
  "summary": "Professional summary or objective (2-3 sentences)",
  "skills": {{
    "technical": ["list of technical skills"],
    "soft": ["list of soft skills"],
    "tools": ["software/tools"]
  }},
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "duration": "Start - End (or Present)",
      "years": 2.5,
      "description": ["Key responsibility 1", "Achievement 2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "institution": "University/College",
      "year": "Graduation year",
      "gpa": "GPA if mentioned"
    }}
  ],
  "certifications": ["Certification 1", "Certification 2"],
  "projects": [
    {{
      "name": "Project name",
      "description": "Brief description",
      "technologies": ["Tech 1", "Tech 2"]
    }}
  ],
  "languages": ["English", "Hindi"],
  "total_experience_years": 5.5
}}

Extract all available information. If something is not found, use empty string or empty array.

Resume Text:
{text[:4000]}  
"""

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert resume parser. Extract information accurately and return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            
            # Clean markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            # Parse JSON
            parsed_data = json.loads(result_text)
            
            # Add metadata
            parsed_data['filename'] = filename
            parsed_data['parsing_method'] = 'openai_api'
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            st.error(f"JSON parsing error: {str(e)}")
            return self._parse_basic(text, filename)
        except Exception as e:
            st.error(f"API parsing error: {str(e)}")
            return self._parse_basic(text, filename)
    
    def _parse_basic(self, text: str, filename: str) -> Dict[str, Any]:
        """Basic regex-based parsing (fallback)"""
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        email = emails[0] if emails else ""
        
        # Extract phone
        phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
        phones = re.findall(phone_pattern, text)
        phone = phones[0] if phones else ""
        
        # Extract name (first line or first few words)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        name = lines[0] if lines else filename.replace('.pdf', '').replace('.docx', '')
        
        # Common skills keywords
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'node', 'sql', 'html', 'css',
            'machine learning', 'data science', 'ai', 'leadership', 'communication',
            'problem solving', 'teamwork', 'git', 'docker', 'aws', 'azure'
        ]
        
        found_skills = []
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        # Estimate experience
        exp_pattern = r'(\d+)\+?\s*(?:years?|yrs?)'
        exp_matches = re.findall(exp_pattern, text.lower())
        total_exp = max([int(e) for e in exp_matches], default=0)
        
        return {
            'filename': filename,
            'name': name,
            'email': email,
            'phone': phone,
            'location': '',
            'summary': text[:200] + '...' if len(text) > 200 else text,
            'skills': {
                'technical': found_skills[:10],
                'soft': [],
                'tools': []
            },
            'experience': [],
            'education': [],
            'certifications': [],
            'projects': [],
            'languages': [],
            'total_experience_years': total_exp,
            'parsing_method': 'basic_regex'
        }
    
    def _get_empty_resume(self) -> Dict[str, Any]:
        """Return empty resume structure"""
        return {
            'filename': '',
            'name': '',
            'email': '',
            'phone': '',
            'location': '',
            'summary': '',
            'skills': {'technical': [], 'soft': [], 'tools': []},
            'experience': [],
            'education': [],
            'certifications': [],
            'projects': [],
            'languages': [],
            'total_experience_years': 0,
            'parsing_method': 'empty'
        }


# Utility function for batch processing
def parse_multiple_resumes(files) -> list:
    """Parse multiple resume files"""
    parser = APIResumeParser()
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, file in enumerate(files):
        status_text.text(f"Parsing {file.name}... ({idx+1}/{len(files)})")
        
        file_content = file.read()
        parsed = parser.parse_resume(file_content, file.name)
        results.append(parsed)
        
        progress_bar.progress((idx + 1) / len(files))
    
    progress_bar.empty()
    status_text.empty()
    
    return results


# Example usage in Streamlit
def demo_parser():
    """Demo page for testing parser"""
    st.title("🚀 Fast Resume Parser (API-Based)")
    
    st.info("✨ This parser uses OpenAI API for accurate results with minimal loading time!")
    
    uploaded_files = st.file_uploader(
        "Upload Resume(s)",
        type=['pdf', 'docx'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("Parse Resumes", type="primary"):
            with st.spinner("Parsing resumes..."):
                results = parse_multiple_resumes(uploaded_files)
            
            st.success(f"✅ Parsed {len(results)} resume(s)")
            
            for result in results:
                with st.expander(f"📄 {result.get('name', 'Unknown')}"):
                    st.json(result)


if __name__ == "__main__":
    demo_parser()