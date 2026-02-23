"""
Session State Manager - Workaround for Streamlit SessionInfo Bug
Author: Claude
Date: Feb 2026

This fixes the "Tried to use SessionInfo before it was initialized" error
by providing a safe wrapper around Streamlit's session state.
"""

import streamlit as st
from typing import Any, Dict, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionManager:
    """
    Safe session state manager that works around Streamlit's SessionInfo bug.
    
    This class provides a fallback mechanism that stores state in a class variable
    if Streamlit's session_state is not yet initialized.
    """
    
    _initialized = False
    _state: Dict[str, Any] = {}
    _defaults: Dict[str, Any] = {
        'initialized': True,
        'parsed_resumes': [],
        'ranked_candidates': [],
        'job_description': "",
        'current_job_id': None,
        'current_job_title': "",
        'page': 'Dashboard',
        'authenticated': False,
        'user_email': None,
        'user_id': None,
        'qa_questions': {},
        'candidate_questions': {},
        'generated_questions': None,
        'selected_candidate_for_questions': None,
        'show_ats_guide': False
    }
    
    @classmethod
    def initialize(cls) -> None:
        """
        Force initialize session state with default values.
        Safe to call multiple times - will only initialize once.
        """
        if cls._initialized:
            return
        
        logger.info("Initializing SessionManager...")
        
        # Store in class variable as backup
        cls._state = cls._defaults.copy()
        
        # Try to store in Streamlit session state
        try:
            if hasattr(st, 'session_state'):
                for key, value in cls._defaults.items():
                    if key not in st.session_state:
                        st.session_state[key] = value
                logger.info("✓ Successfully initialized Streamlit session_state")
            else:
                logger.warning("⚠ Streamlit session_state not available - using fallback")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Streamlit session_state: {e}")
            logger.info("Using class variable fallback")
        
        cls._initialized = True
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Safely get a value from session state.
        
        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The value from session state, or default if not found
        """
        # Ensure initialized
        cls.initialize()
        
        # Try Streamlit session state first
        try:
            if hasattr(st, 'session_state') and hasattr(st.session_state, key):
                return getattr(st.session_state, key)
        except Exception as e:
            logger.debug(f"Could not get '{key}' from Streamlit session_state: {e}")
        
        # Fallback to class variable
        return cls._state.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        Safely set a value in session state.
        
        Args:
            key: The key to set
            value: The value to store
        """
        # Ensure initialized
        cls.initialize()
        
        # Update class backup
        cls._state[key] = value
        
        # Try to update Streamlit session state
        try:
            if hasattr(st, 'session_state'):
                setattr(st.session_state, key, value)
                # Verify it was set
                if hasattr(st.session_state, key):
                    logger.debug(f"✓ Set '{key}' in Streamlit session_state")
                else:
                    logger.warning(f"⚠ Failed to verify '{key}' in Streamlit session_state")
        except Exception as e:
            logger.warning(f"Could not set '{key}' in Streamlit session_state: {e}")
            logger.info("Value stored in class variable fallback")
    
    @classmethod
    def delete(cls, key: str) -> None:
        """
        Safely delete a key from session state.
        
        Args:
            key: The key to delete
        """
        # Delete from class backup
        if key in cls._state:
            del cls._state[key]
        
        # Try to delete from Streamlit session state
        try:
            if hasattr(st, 'session_state') and hasattr(st.session_state, key):
                delattr(st.session_state, key)
        except Exception as e:
            logger.warning(f"Could not delete '{key}' from Streamlit session_state: {e}")
    
    @classmethod
    def clear(cls) -> None:
        """Clear all session state (except defaults)."""
        cls._state = cls._defaults.copy()
        
        try:
            if hasattr(st, 'session_state'):
                for key in list(st.session_state.keys()):
                    if key not in cls._defaults:
                        delattr(st.session_state, key)
        except Exception as e:
            logger.warning(f"Could not clear Streamlit session_state: {e}")
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Get all session state as dictionary."""
        cls.initialize()
        
        try:
            if hasattr(st, 'session_state'):
                return {k: getattr(st.session_state, k) for k in dir(st.session_state) 
                       if not k.startswith('_')}
        except Exception:
            pass
        
        return cls._state.copy()
    
    @classmethod
    def has_key(cls, key: str) -> bool:
        """Check if a key exists in session state."""
        try:
            if hasattr(st, 'session_state') and hasattr(st.session_state, key):
                return True
        except Exception:
            pass
        
        return key in cls._state
    
    @classmethod
    def reset_to_defaults(cls) -> None:
        """Reset session state to default values."""
        cls._initialized = False
        cls.initialize()


# Auto-initialize on import
SessionManager.initialize()


# Convenience functions for easier usage
def get_session(key: str, default: Any = None) -> Any:
    """Convenience function to get from session."""
    return SessionManager.get(key, default)


def set_session(key: str, value: Any) -> None:
    """Convenience function to set in session."""
    SessionManager.set(key, value)


def delete_session(key: str) -> None:
    """Convenience function to delete from session."""
    SessionManager.delete(key)


def clear_session() -> None:
    """Convenience function to clear session."""
    SessionManager.clear()


def has_session_key(key: str) -> bool:
    """Convenience function to check if key exists."""
    return SessionManager.has_key(key)


# Example usage:
if __name__ == "__main__":
    # Test the session manager
    print("Testing SessionManager...")
    
    # Set some values
    set_session('test_key', 'test_value')
    set_session('test_number', 42)
    
    # Get values
    print(f"test_key: {get_session('test_key')}")
    print(f"test_number: {get_session('test_number')}")
    print(f"missing_key: {get_session('missing_key', 'default_value')}")
    
    # Check if key exists
    print(f"Has test_key: {has_session_key('test_key')}")
    print(f"Has missing_key: {has_session_key('missing_key')}")
    
    # Get all session data
    print(f"All session data: {SessionManager.get_all()}")
    
    print("✓ SessionManager test complete!")