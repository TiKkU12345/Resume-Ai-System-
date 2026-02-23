"""
Improved Skills Extraction - Quick Fix
"""

import re
from typing import Dict, List


def extract_skills_enhanced(text: str) -> Dict[str, List[str]]:
    """
    Enhanced skills extraction that actually works!
    """
    skills = {
        'programming_languages': [],
        'ml_ai': [],
        'frameworks': [],
        'cloud_tools': [],
        'databases': [],
        'other': []
    }
    
    # Comprehensive skill mapping
    skill_mapping = {
        'programming_languages': [
            'python', 'java', 'javascript', 'sql', 'numpy', 'pandas', 
            'scikit-learn', 'sklearn', 'c++', 'r', 'typescript', 'c#',
            'ruby', 'php', 'swift', 'kotlin', 'go'
        ],
        'ml_ai': [
            'machine learning', 'deep learning', 'nlp', 'natural language processing',
            'computer vision', 'cnn', 'rnn', 'lstm', 'transformer', 'transformers',
            'opencv', 'yolo', 'spacy', 'bert', 'gpt', 'hugging face',
            'neural network', 'data science', 'ai'
        ],
        'frameworks': [
            'tensorflow', 'pytorch', 'keras', 'flask', 'fastapi', 'streamlit',
            'django', 'react', 'node.js', 'express', 'angular', 'vue',
            'spring', 'springboot', 'laravel'
        ],
        'cloud_tools': [
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 
            'git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'terraform'
        ],
        'databases': [
            'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 
            'dynamodb', 'cassandra', 'oracle', 'sql server'
        ]
    }
    
    text_lower = text.lower()
    
    # Search for each skill in the text
    for category, skill_list in skill_mapping.items():
        for skill in skill_list:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                # Capitalize properly
                formatted_skill = skill.title()
                if formatted_skill not in skills[category]:
                    skills[category].append(formatted_skill)
    
    return skills