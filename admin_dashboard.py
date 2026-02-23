"""
Admin Dashboard for User Approval - Streamlit Version
Beautiful admin interface to manage user signups and approvals
"""

import streamlit as st
from database import SupabaseManager
from datetime import datetime
import pandas as pd


def render_admin_dashboard():
    """Render complete admin dashboard"""
    
    # Check if user is admin
    if not st.session_state.get('is_admin', False):
        st.error("⛔ Access Denied: Admin privileges required")
        st.info("This page is only accessible to administrators.")
        return
    
    st.title("👑 Admin Dashboard")
    st.markdown("**Manage User Approvals and System Settings**")
    st.markdown("---")
    
    db = SupabaseManager()
    
    # Get stats
    try:
        all_users = db.get_all_users()
        pending_users = [u for u in all_users if not u.get('is_approved', False)]
        approved_users = [u for u in all_users if u.get('is_approved', False)]
    except Exception as e:
        st.error(f"Failed to load users: {str(e)}")
        return
    
    # Stats Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; color: white; text-align: center;'>
            <h3 style='margin: 0; color: white;'>⏳ Pending</h3>
            <h1 style='margin: 10px 0; color: white;'>{}</h1>
        </div>
        """.format(len(pending_users)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    padding: 20px; border-radius: 10px; color: white; text-align: center;'>
            <h3 style='margin: 0; color: white;'>✅ Approved</h3>
            <h1 style='margin: 10px 0; color: white;'>{}</h1>
        </div>
        """.format(len(approved_users)), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                    padding: 20px; border-radius: 10px; color: white; text-align: center;'>
            <h3 style='margin: 0; color: white;'>👥 Total Users</h3>
            <h1 style='margin: 10px 0; color: white;'>{}</h1>
        </div>
        """.format(len(all_users)), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2 = st.tabs(["⏳ Pending Approvals", "👥 All Users"])
    
    with tab1:
        render_pending_users(db, pending_users)
    
    with tab2:
        render_all_users(db, all_users)


def render_pending_users(db, pending_users):
    """Render pending users for approval"""
    st.markdown("### ⏳ Pending User Approvals")
    
    if not pending_users:
        st.info("🎉 No pending approvals! All users are processed.")
        return
    
    st.markdown(f"**{len(pending_users)} user(s) waiting for approval**")
    st.markdown("---")
    
    for user in pending_users:
        render_user_approval_card(db, user)


def render_user_approval_card(db, user):
    """Render individual user card with approve/reject buttons"""
    
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### 👤 {user.get('full_name', 'Unknown')}")
            st.markdown(f"📧 **Email:** {user.get('email', 'N/A')}")
            
            created_at = user.get('created_at', '')
            if created_at:
                try:
                    # Handle both ISO format with/without Z
                    dt_str = created_at.replace('Z', '+00:00') if 'Z' in created_at else created_at
                    dt = datetime.fromisoformat(dt_str)
                    formatted_date = dt.strftime('%B %d, %Y at %I:%M %p')
                    st.markdown(f"📅 **Signed up:** {formatted_date}")
                except:
                    st.markdown(f"📅 **Signed up:** {created_at}")
            
            device_id = user.get('device_id', 'N/A')
            if device_id and len(device_id) > 16:
                st.markdown(f"🔧 **Device:** `{device_id[:16]}...`")
            else:
                st.markdown(f"🔧 **Device:** `{device_id}`")
        
        with col2:
            st.write("")
            st.write("")
            if st.button("✅ Approve", key=f"approve_{user['id']}", 
                        type="primary", use_container_width=True):
                approve_user(db, user)
        
        with col3:
            st.write("")
            st.write("")
            if st.button("❌ Reject", key=f"reject_{user['id']}", 
                        use_container_width=True):
                reject_user(db, user)
        
        st.markdown("---")


def approve_user(db, user):
    """Approve a user"""
    try:
        admin_email = st.session_state.get('user_email', 'admin')
        
        # Update user in database
        success = db.approve_user(
            user['id'],
            admin_email,
            user.get('device_id')
        )
        
        if success:
            st.success(f"✅ {user['full_name']} has been approved!")
            
            # Send approval email
            send_approval_email(user['email'], user['full_name'])
            
            # Delay then rerun
            import time
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to approve user")
            
    except Exception as e:
        st.error(f"Approval failed: {str(e)}")


def reject_user(db, user):
    """Reject and delete a user"""
    try:
        success = db.delete_user(user['id'])
        
        if success:
            st.success(f"User {user['full_name']} has been rejected and deleted.")
            import time
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to delete user")
            
    except Exception as e:
        st.error(f"Rejection failed: {str(e)}")


def render_all_users(db, all_users):
    """Render table of all users"""
    st.markdown("### 👥 All Users")
    
    if not all_users:
        st.info("No users in the system yet.")
        return
    
    # Create DataFrame
    user_data = []
    for user in all_users:
        user_data.append({
            'Name': user.get('full_name', 'Unknown'),
            'Email': user.get('email', 'N/A'),
            'Status': '✅ Approved' if user.get('is_approved', False) else '⏳ Pending',
            'Admin': '🔑 Yes' if user.get('is_admin', False) else 'No',
            'Joined': user.get('created_at', '')[:10] if user.get('created_at') else 'N/A'
        })
    
    df = pd.DataFrame(user_data)
    
    # Display with filters
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "Approved", "Pending"]
        )
    
    with col2:
        st.write("")
    
    if filter_status == "Approved":
        df = df[df['Status'] == '✅ Approved']
    elif filter_status == "Pending":
        df = df[df['Status'] == '⏳ Pending']
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Download options
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download as CSV",
            data=csv,
            file_name=f"users_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )


def send_approval_email(email, name):
    """Send approval notification email"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Get SMTP config from Streamlit secrets
        try:
            sender_email = st.secrets.get('SMTP_EMAIL', 'your_email@gmail.com')
            sender_password = st.secrets.get('SMTP_PASSWORD', 'your_app_password')
        except:
            st.warning("Email configuration not found in secrets. Skipping email notification.")
            return
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Account Approved! - AI Resume System"
        
        body = f"""
        Hi {name},
        
        Great news! Your account has been approved by the administrator.
        
        You can now log in to the AI Resume Shortlisting System and start using all features.
        
        Login here: http://localhost:8501
        
        Best regards,
        AI Resume Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        st.info(f"✉️ Approval email sent to {email}")
        
    except Exception as e:
        st.warning(f"Could not send email: {str(e)}")
        st.info("User approved, but email notification failed.")


# Standalone page for direct access
if __name__ == "__main__":
    st.set_page_config(page_title="Admin Dashboard", page_icon="👑", layout="wide")
    render_admin_dashboard()