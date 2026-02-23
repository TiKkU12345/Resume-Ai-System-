"""
Resource Manager - Centralized instance creation
Provides singleton-like access to shared resources
"""

from resume_parser import ResumeParser
from job_resume_matcher import CandidateRanker, JobDescriptionParser
from generate_question import QuestionGenerator, AnswerEvaluator
from database import SupabaseManager

# Cache instances to avoid recreating

_instances = {}



def get_resume_parser():
    """Get or create ResumeParser instance"""
    if 'parser' not in _instances:
        _instances['parser'] = ResumeParser()
    return _instances['parser']

def get_ranker():
    """Get or create CandidateRanker instance"""
    if 'ranker' not in _instances:
        _instances['ranker'] = CandidateRanker()
    return _instances['ranker']

def get_job_parser():
    """Get or create JobDescriptionParser instance"""
    if 'job_parser' not in _instances:
        _instances['job_parser'] = JobDescriptionParser()
    return _instances['job_parser']

def get_question_generator():
    """Get or create QuestionGenerator instance"""
    if 'question_gen' not in _instances:
        try:
            _instances['question_gen'] = QuestionGenerator()
        except Exception as e:
            print(f"QuestionGenerator initialization failed: {e}")
            _instances['question_gen'] = None
    return _instances['question_gen']

def get_answer_evaluator():
    """Get or create AnswerEvaluator instance"""
    if 'answer_eval' not in _instances:
        try:
            _instances['answer_eval'] = AnswerEvaluator()
        except Exception as e:
            print(f"AnswerEvaluator initialization failed: {e}")
            _instances['answer_eval'] = None
    return _instances['answer_eval']

def get_supabase():
    """Get or create SupabaseManager instance"""
    if 'supabase' not in _instances:
        try:
            _instances['supabase'] = SupabaseManager()
        except Exception as e:
            print(f"SupabaseManager initialization failed: {e}")
            _instances['supabase'] = None
    return _instances['supabase']

def clear_cache():
    """Clear all cached instances"""
    _instances.clear()