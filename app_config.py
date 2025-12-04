"""
Configuration Helper
Handles secrets for both Streamlit Cloud and Hugging Face Spaces
"""

import os
import streamlit as st


def get_secret(key: str, default=None):
    """
    Get secret from environment variables or Streamlit secrets
    
    Priority:
    1. Environment variables (Hugging Face Spaces, Railway, Render)
    2. Streamlit secrets (Streamlit Cloud, local development)
    3. Default value
    
    Args:
        key: Secret key name
        default: Default value if secret not found
    
    Returns:
        Secret value or default
    """
    # Try environment variable first (Hugging Face, Render, Railway)
    value = os.getenv(key)
    if value:
        return value
    
    # Fall back to Streamlit secrets (Streamlit Cloud, local)
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        if default is None:
            # Only warn if no default provided
            st.warning(f"⚠️ Secret '{key}' not found. Please configure it.")
        return default


def get_all_secrets():
    """Get all configured secrets (for debugging)"""
    secrets = {}
    
    # Common secret keys
    keys = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'OPENAI_API_KEY',
        'ADMIN_EMAIL',
        'MONGODB_URI',
        'MONGODB_DATABASE'
    ]
    
    for key in keys:
        value = get_secret(key)
        if value:
            # Mask sensitive values
            if len(value) > 10:
                secrets[key] = value[:4] + '...' + value[-4:]
            else:
                secrets[key] = '***'
        else:
            secrets[key] = None
    
    return secrets


def check_required_secrets(required_keys: list) -> tuple:
    """
    Check if all required secrets are configured
    
    Args:
        required_keys: List of required secret keys
    
    Returns:
        (all_present: bool, missing_keys: list)
    """
    missing = []
    
    for key in required_keys:
        value = get_secret(key)
        if not value:
            missing.append(key)
    
    return len(missing) == 0, missing


def display_config_status():
    """Display configuration status in Streamlit"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Configuration")
    
    secrets = get_all_secrets()
    
    for key, value in secrets.items():
        if value and value != 'None':
            st.sidebar.success(f"✅ {key}")
        else:
            st.sidebar.error(f"❌ {key}")


# Example usage
if __name__ == "__main__":
    st.title("Configuration Helper Test")
    
    st.header("Configured Secrets")
    secrets = get_all_secrets()
    
    for key, value in secrets.items():
        if value:
            st.success(f"✅ {key}: {value}")
        else:
            st.error(f"❌ {key}: Not configured")
    
    st.header("Check Required Secrets")
    required = ['SUPABASE_URL', 'SUPABASE_KEY', 'OPENAI_API_KEY']
    all_present, missing = check_required_secrets(required)
    
    if all_present:
        st.success("✅ All required secrets are configured!")
    else:
        st.error(f"❌ Missing secrets: {', '.join(missing)}")