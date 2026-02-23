"""
ATS Resume Format Helper
Validates and guides users to upload ATS-friendly resumes
"""

import streamlit as st
import re
from typing import Dict, List, Tuple


class ATSResumeValidator:
    """Validates if resume follows ATS-friendly format"""
    
    # ATS-friendly section headers (English)
    ATS_SECTIONS = {
        'contact': ['contact', 'personal', 'profile', 'about'],
        'summary': ['summary', 'objective', 'profile summary', 'professional summary'],
        'experience': ['experience', 'work experience', 'employment', 'work history', 'professional experience'],
        'education': ['education', 'academic', 'qualification', 'qualifications'],
        'skills': ['skills', 'skills', 'core competencies', 'expertise', 'technologies'],
        'projects': ['projects', 'key projects', 'major projects'],
        'certifications': ['certifications', 'certificates', 'licenses']
    }
    
    def __init__(self):
        self.issues = []
        self.score = 100
    
    def validate_resume(self, parsed_data: Dict) -> Tuple[bool, int, List[str]]:
        """
        Validate if resume is ATS-friendly
        
        Returns:
            (is_ats_friendly, score, issues_list)
        """
        self.issues = []
        self.score = 100
        
        # Check 1: Contact Information
        if not self._check_contact_info(parsed_data):
            self.issues.append("❌ Contact information missing or incomplete")
            self.score -= 20
        
        # Check 2: Clear Sections
        if not self._check_sections(parsed_data):
            self.issues.append("⚠️ Standard sections not clearly defined")
            self.score -= 15
        
        # Check 3: Skills Section
        if not self._check_skills(parsed_data):
            self.issues.append("❌ Skills section missing or poorly formatted")
            self.score -= 15
        
        # Check 4: Work Experience
        if not self._check_experience(parsed_data):
            self.issues.append("⚠️ Work experience section needs improvement")
            self.score -= 15
        
        # Check 5: Education
        if not self._check_education(parsed_data):
            self.issues.append("⚠️ Education section missing or incomplete")
            self.score -= 10
        
        # Check 6: Dates in proper format
        if not self._check_date_formats(parsed_data):
            self.issues.append("⚠️ Dates should be in standard format (MM/YYYY)")
            self.score -= 10
        
        # Check 7: No complex formatting
        if not self._check_simple_formatting(parsed_data):
            self.issues.append("⚠️ Complex formatting detected - use simple text")
            self.score -= 15
        
        is_ats_friendly = self.score >= 70
        
        return is_ats_friendly, self.score, self.issues
    
    def _check_contact_info(self, data: Dict) -> bool:
        """Check if contact info is complete"""
        contact = data.get('contact', {})
        has_name = bool(contact.get('name'))
        has_email = bool(contact.get('email'))
        has_phone = bool(contact.get('phone'))
        
        return has_name and has_email and has_phone
    
    def _check_sections(self, data: Dict) -> bool:
        """Check if resume has standard sections"""
        required_sections = ['contact', 'experience', 'education', 'skills']
        found_sections = 0
        
        for section in required_sections:
            if data.get(section):
                found_sections += 1
        
        return found_sections >= 3  # At least 3 out of 4
    
    def _check_skills(self, data: Dict) -> bool:
        """Check if skills are properly listed"""
        skills = data.get('skills', {})
        
        if not skills:
            return False
        
        # Count total skills
        total_skills = sum(len(v) for v in skills.values() if isinstance(v, list))
        return total_skills >= 5  # At least 5 skills
    
    def _check_experience(self, data: Dict) -> bool:
        """Check if experience is properly formatted"""
        experience = data.get('experience', [])
        
        if not experience:
            return False
        
        # Check if at least one job has required fields
        for job in experience:
            if job.get('company') and job.get('title'):
                return True
        
        return False
    
    def _check_education(self, data: Dict) -> bool:
        """Check if education is listed"""
        education = data.get('education', [])
        return len(education) > 0
    
    def _check_date_formats(self, data: Dict) -> bool:
        """Check if dates are in standard format"""
        # This is a simplified check
        # In real implementation, check actual date formats
        return True  # For now, assume dates are okay
    
    def _check_simple_formatting(self, data: Dict) -> bool:
        """Check if formatting is simple (not complex)"""
        # Check if we successfully parsed most information
        # Complex PDFs with tables, columns fail to parse well
        
        contact = data.get('contact', {})
        experience = data.get('experience', [])
        education = data.get('education', [])
        
        # If we got good data, formatting is probably simple
        return bool(contact) and (len(experience) > 0 or len(education) > 0)


def render_ats_guide():
    """Render ATS resume format guide"""
    st.markdown("## 📋 ATS-Friendly Resume Guide")
    
    st.info("""
    **This system supports ATS (Applicant Tracking System) format resumes.**
    
    ATS-friendly resume:
    ✅ resume parsing
    ✅ Accurate matching and ranking 
    ✅ Every ATS system can read it easily
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ (DO's)")
        st.markdown("""
        **1. Simple Format Use :**
        - Plain text format
        - Standard fonts (Arial, Calibri, Times New Roman)
        - Single column layout
        - Clear section headings
        
        **2. Standard Sections Include :**
        - Contact Information
        - Professional Summary
        - Work Experience
        - Education
        - Skills
        - Certifications (if any)
        
        **3. Clear Headers Use :**
        ```
        WORK EXPERIENCE
        EDUCATION
        SKILLS
        CERTIFICATIONS
        ```
        
        **4. Dates are in Standard Format:**
        - MM/YYYY format (e.g., 01/2020 - 12/2023)
        - Month YYYY (e.g., Jan 2020 - Dec 2023)

        **5. Skills are Clearly Listed:**
        ```
        Skills:
        • Python, Java, JavaScript
        • AWS, Docker, Kubernetes
        • MySQL, PostgreSQL
        • React, Node.js
        ```
        """)
    
    with col2:
        st.markdown("### ❌ (DON'Ts)")
        st.markdown("""
        **1. Complex Formatting:**
        - ❌ Tables
        - ❌ Text boxes
        - ❌ Multiple columns
        - ❌ Headers/Footers with important info
        - ❌ Images or photos
        
        **2. Fancy Graphics:**
        - ❌ Charts or graphs
        - ❌ Icons
        - ❌ Decorative elements
        - ❌ Color coding
        
        **3. Non-Standard Fonts:**
        - ❌ Cursive fonts
        - ❌ Very small text (<10pt)
        - ❌ Decorative fonts
        
        **4. Abbreviations Without Explanation:**
        - ❌ ML (explain: Machine Learning)
        - ✅ ML (Machine Learning)
        
        **5. Skills are Clearly Listed:**
        - ❌ Skill bars or rating graphs
        - ✅ Simple bullet points
        """)
    
    st.markdown("---")
    
    # Download ATS Template
    st.markdown("### 📥 Use ATS Resume Template Download ")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download Word Template", use_container_width=True):
            st.info("Template coming soon! For now, follow the guidelines above.")
    
    with col2:
        if st.button("📄 Download PDF Template", use_container_width=True):
            st.info("Template coming soon! For now, follow the guidelines above.")
    
    with col3:
        if st.button("📺 Watch Tutorial Video", use_container_width=True):
            st.info("Tutorial coming soon!")
    
    st.markdown("---")
    
    # Example ATS Resume Structure
    with st.expander("📖 Example ATS-Friendly Resume Structure"):
        st.code("""
ARUNAV KUMAR
Email: arunav11a31.hts21@gmail.com | Phone: +91 8002933460
LinkedIn: linkedin.com/in/arunav-kumar

PROFESSIONAL SUMMARY
AI/ML Engineer with 3+ years of experience in developing and deploying machine 
learning models. Expertise in Python, TensorFlow, and cloud platforms.

EXPERIENCE

Senior ML Engineer | TechCorp India | Jan 2022 - Present
• Developed and deployed 15+ ML models in production
• Improved model accuracy by 25% through hyperparameter tuning
• Led team of 3 junior engineers

ML Engineer | DataSolutions Pvt Ltd | Jun 2020 - Dec 2021
• Built recommendation system serving 1M+ users
• Implemented CI/CD pipeline for ML models
• Reduced inference time by 40%

EDUCATION

B.Tech in Computer Science | IIT Delhi | 2016 - 2020
CGPA: 8.5/10

SKILLS

Programming Languages: Python, Java, JavaScript, SQL
ML/AI: TensorFlow, PyTorch, Scikit-learn, Keras
Cloud: AWS (SageMaker, EC2, S3), Google Cloud Platform
Tools: Docker, Kubernetes, Git, Jenkins
Databases: MySQL, PostgreSQL, MongoDB

CERTIFICATIONS

• AWS Certified Machine Learning - Specialty (2023)
• TensorFlow Developer Certificate (2022)
• Google Cloud Professional ML Engineer (2021)

PROJECTS

Customer Churn Prediction System
• Built ML model with 92% accuracy to predict customer churn
• Deployed on AWS Lambda for real-time predictions
• Technologies: Python, XGBoost, AWS

Sentiment Analysis API
• Developed REST API for sentiment analysis
• Processed 100K+ texts daily
• Technologies: Python, BERT, FastAPI, Docker
        """)


def validate_and_show_feedback(parsed_resume: Dict):
    """Validate resume and show feedback to user"""
    validator = ATSResumeValidator()
    is_ats, score, issues = validator.validate_resume(parsed_resume)
    
    st.markdown("### 📊 ATS Compatibility Score")
    
    # Show score with color
    if score >= 80:
        st.success(f"✅ **Excellent!** ATS Score: {score}/100")
    elif score >= 60:
        st.warning(f"⚠️ **Good, but can improve** ATS Score: {score}/100")
    else:
        st.error(f"❌ **Needs improvement** ATS Score: {score}/100")
    
    # Show progress bar
    st.progress(score / 100)
    
    # Show issues if any
    if issues:
        st.markdown("#### 🔍 Issues Found:")
        for issue in issues:
            st.markdown(f"- {issue}")
        
        st.info("💡 **Tip:** Upload an ATS-friendly resume for better results. Click 'ATS Guide' for help.")
    else:
        st.success("🎉 Your resume is perfectly formatted for ATS!")
    
    return is_ats, score


def show_ats_warning():
    """Show warning about ATS format before upload"""
    st.warning("""
    ⚠️ **Important: Please upload ATS-friendly resumes**
    
    This system supports ATS (Applicant Tracking System) format resumes.
    
    - ✅ Simple formatting
    - ✅ Clear section headers
    - ✅ No tables or columns
    - ✅ Standard fonts

    Please review the ATS Resume Guide before uploading your resume! 👇
    """)
    
    if st.button("📖 View ATS Resume Guide", use_container_width=True):
        st.session_state.show_ats_guide = True