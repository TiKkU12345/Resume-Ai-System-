
import streamlit as st
from supabase import create_client, Client
import hashlib
from datetime import datetime
import re


# AUTHORIZED EMAILS CONFIGURATION

AUTHORIZED_EMAILS = [
    "arunav.jsr.0604@gmail.com",
    "admin@company.com",
    "hr@company.com",
]

AUTHORIZED_DOMAINS = [
    "6801788@rungta.org",
    "@yourcompany.com",
]

AUTH_MODE = 'both'


def is_email_authorized(email):
    """Check if email is authorized"""
    email = email.lower().strip()
    
    if AUTH_MODE == 'emails':
        if email in [e.lower() for e in AUTHORIZED_EMAILS]:
            return True, "Email authorized"
        return False, "This email is not authorized. Contact admin for access."
    
    elif AUTH_MODE == 'domains':
        for domain in AUTHORIZED_DOMAINS:
            if email.endswith(domain.lower()):
                return True, "Domain authorized"
        return False, f"Only emails from authorized domains are allowed: {', '.join(AUTHORIZED_DOMAINS)}"
    
    elif AUTH_MODE == 'both':
        if email in [e.lower() for e in AUTHORIZED_EMAILS]:
            return True, "Email authorized"
        
        for domain in AUTHORIZED_DOMAINS:
            if email.endswith(domain.lower()):
                return True, "Domain authorized"
        
        return False, f"Unauthorized email. Only specific emails or domains {', '.join(AUTHORIZED_DOMAINS)} are allowed."
    
    return False, "Invalid authorization mode"


def validate_email_format(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def get_supabase_client():
    """Get Supabase client from secrets"""
    try:
        url = st.secrets["SUPABASE_URL"]
        
        try:
            key = st.secrets["SUPABASE_SERVICE_KEY"]
        except KeyError:
            key = st.secrets["SUPABASE_KEY"]
        
        return create_client(url, key)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {str(e)}")
        return None


class AuthManager:
    """Manages user authentication with email whitelist"""
    
    def __init__(self):
        self._supabase = None
        self._connection_error = None
    
    @property
    def supabase(self):
        """Lazy load Supabase client"""
        if self._supabase is None and self._connection_error is None:
            try:
                self._supabase = get_supabase_client()
                if self._supabase is None:
                    self._connection_error = "Failed to initialize Supabase"
            except Exception as e:
                self._connection_error = str(e)
        
        return self._supabase
    
    def signup(self, email, password):
        """Sign up a new user (only if authorized)"""
        if not validate_email_format(email):
            return False, "Invalid email format"
        
        is_authorized, auth_message = is_email_authorized(email)
        if not is_authorized:
            return False, f"🚫 {auth_message}"
        
        if not self.supabase:
            return False, "Database connection unavailable"
        
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                if response.session:
                    return True, "✅ Account created successfully! You can now login."
                else:
                    return True, "✅ Account created! Please check your email to verify your account."
            else:
                return False, "Failed to create account. Please try again."
            
        except Exception as e:
            error_msg = str(e)
            
            if "User already registered" in error_msg:
                return False, "This email is already registered. Please login instead."
            elif "Invalid email" in error_msg:
                return False, "Invalid email address format."
            elif "Password should be at least" in error_msg:
                return False, "Password must be at least 6 characters long."
            elif "SMTP" in error_msg or "email" in error_msg.lower():
                st.warning("⚠️ Email service unavailable. Your account is created but email verification is disabled.")
                return True, "Account created! You can login directly (email verification skipped)."
            else:
                return False, f"Signup failed: {error_msg}"
    
    def login(self, email, password):
        """
        Login user (only if authorized)
        CRITICAL FIX: Safe session state access
        """
        is_authorized, auth_message = is_email_authorized(email)
        if not is_authorized:
            return False, f"🚫 {auth_message}", None
        
        if not self.supabase:
            return False, "Database connection unavailable", None
        
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # CRITICAL FIX: Safe session state update
                # Ensure session state is initialized before accessing
                if 'authenticated' not in st.session_state:
                    # Emergency initialization if somehow missing
                    st.session_state.authenticated = False
                    st.session_state.user_email = None
                    st.session_state.user_id = None
                
                # Now safely update
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_id = response.user.id
                
                return True, "Login successful!", response.user
            else:
                return False, "Login failed. Please check your credentials.", None
                
        except Exception as e:
            error_msg = str(e)
            
            if "Invalid login credentials" in error_msg:
                return False, "Invalid email or password.", None
            elif "Email not confirmed" in error_msg:
                return False, "Please verify your email before logging in. Check your inbox.", None
            else:
                return False, f"Login failed: {error_msg}", None
    
    def logout(self):
        """Logout current user"""
        try:
            if self.supabase:
                self.supabase.auth.sign_out()
            
            # Clear session state safely
            if hasattr(st, 'session_state'):
                st.session_state.authenticated = False
                st.session_state.user_email = None
                st.session_state.user_id = None
            
            return True, "Logged out successfully"
        except Exception as e:
            return False, f"Logout failed: {str(e)}"
    
    def is_authenticated(self):
        """
        Check if user is authenticated
        CRITICAL FIX: Safe session state check
        """
        # Safety check - ensure session_state exists
        if not hasattr(st, 'session_state'):
            return False
        
        return st.session_state.get('authenticated', False)
    
    def reset_password(self, email):
        """Send password reset email"""
        if not self.supabase:
            return False, "Database connection unavailable"
        
        try:
            self.supabase.auth.reset_password_for_email(email)
            return True, "Password reset email sent! Check your inbox."
        except Exception as e:
            return False, f"Failed to send reset email: {str(e)}"
    
    def resend_verification(self, email):
        """Resend verification email"""
        if not self.supabase:
            return False, "Database connection unavailable"
        
        try:
            self.supabase.auth.resend({"type": "signup", "email": email})
            return True, "Verification email resent! Check your inbox."
        except Exception as e:
            return False, f"Failed to resend verification: {str(e)}"



def render_auth_page():
    """Render beautiful authentication page"""
    
    # CRITICAL: Initialize session state FIRST if not already done
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_id = None
    
    # Custom CSS
    st.markdown("""
        <style>
        .auth-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
        }
        .auth-notice {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
            text-align: center;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            justify-content: center;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 1rem 2rem;
        }
        .copyright-footer {
            text-align: center;
            margin-top: 3rem;
            padding: 1rem;
            color: #888;
            font-size: 0.85rem;
        }
        .copyright-footer .line1 {
            font-weight: 500;
            margin-bottom: 0.25rem;
        }
        .copyright-footer .line2 {
            font-size: 0.8rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("<h1>🎯 AI Resume Shortlisting</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888; margin-bottom: 1rem;'>Sign in to access your recruitment dashboard</p>", unsafe_allow_html=True)
    
    # Authorization notice
    if AUTH_MODE == 'emails':
        auth_info = "Only authorized email addresses can access this system. Contact administrator for access if you need it."
    elif AUTH_MODE == 'domains':
        auth_info = f"Only emails from authorized domains can access this system. Contact administrator for access if you need it."
    else:
        auth_info = f"Only authorized emails or domains can access this system. Contact administrator for access if you need it."
    
    st.markdown(f"""
        <div class="auth-notice">
            <strong>🔒 Restricted Access:</strong> {auth_info}
        </div>
    """, unsafe_allow_html=True)
    
    # Tabs for Login and Signup
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    auth_manager = AuthManager()
    
    # LOGIN TAB
    with tab1:
        with st.form("login_form"):
            st.markdown("### Login to Your Account")
            st.markdown("")
            
            email = st.text_input("Email", placeholder="your-email@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            st.markdown("")
            col1, col2 = st.columns(2)
            
            with col1:
                submit = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")
            
            with col2:
                forgot_password = st.form_submit_button("🔑 Forgot Password?", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    with st.spinner("Logging in..."):
                        success, message, user = auth_manager.login(email, password)
                        
                        if success:
                            st.success(message)
                            st.info("✅ Login successful! Page will refresh automatically.")
                            st.rerun()
                        else:
                            st.error(message)
            
            if forgot_password:
                if not email:
                    st.error("Please enter your email first")
                else:
                    success, message = auth_manager.reset_password(email)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    # SIGNUP TAB
    with tab2:
        with st.form("signup_form"):
            st.markdown("### Create Account")
            st.markdown("")
            
            full_name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="your-email@company.com")
            
            if AUTH_MODE == 'domains':
                st.caption(f"📧 Use an email from: {', '.join(AUTHORIZED_DOMAINS)}")
            elif AUTH_MODE == 'emails':
                st.caption("📧 Only authorized emails can signup")
            
            password = st.text_input("Password", type="password", placeholder="••••••••", help="Minimum 6 characters")
            password_confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")
            
            st.markdown("")
            agree = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            st.markdown("")
            submit = st.form_submit_button("✨ Create Account", use_container_width=True, type="primary")
            
            if submit:
                if not full_name or not email or not password or not password_confirm:
                    st.error("Please fill all fields")
                elif not agree:
                    st.error("Please agree to Terms of Service")
                elif password != password_confirm:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    with st.spinner("Creating account..."):
                        success, message = auth_manager.signup(email, password)
                        
                        if success:
                            st.success(f"Welcome {full_name}! {message}")
                            st.info("💡 You can now go to the Login tab and sign in!")
                        else:
                            st.error(message)
                            
                            if "🚫" in message or "Unauthorized" in message:
                                st.warning("💼 Need access? Contact your administrator to add your email to the authorized list.")
    
    # Copyright Footer
    current_year = datetime.now().year
    
    st.markdown(f"""
        <div class="copyright-footer">
            <div class="line1">Powered by AI & Machine Learning</div>
            <div class="line2">© {current_year} Resume Shortlisting System. All Rights Reserved.</div>
        </div>
    """, unsafe_allow_html=True)


def render_auth_sidebar():
    """
    Render authentication info in sidebar
    CRITICAL FIX: Safe session state check
    """
    
    # Safety check - ensure session_state exists
    if not hasattr(st, 'session_state'):
        return
    
    if st.session_state.get('authenticated', False):
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 Logged In")
            
            user_email = st.session_state.get('user_email', 'Unknown')
            st.info(f"📧 {user_email}")
            
            if st.button("🚪 Logout", use_container_width=True):
                auth_manager = AuthManager()
                success, message = auth_manager.logout()
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


def require_auth(func):
    """
    Decorator to require authentication for a function
    Usage: @require_auth
    """
    def wrapper(*args, **kwargs):
        auth_manager = AuthManager()
        if not auth_manager.is_authenticated():
            render_auth_page()
            st.stop()
            return None
        return func(*args, **kwargs)
    return wrapper
