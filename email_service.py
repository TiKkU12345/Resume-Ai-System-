"""
Email Service for Admin Approval Notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app_config import get_secret


class EmailService:
    """Handle email notifications for user approvals"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = get_secret("SENDER_EMAIL", "your-email@gmail.com")
        self.sender_password = get_secret("SENDER_APP_PASSWORD", "")
        
    def send_approval_email(self, user_email: str, user_name: str) -> tuple:
        """
        Send approval notification to user
        Returns: (success: bool, message: str)
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = user_email
            msg['Subject'] = "🎉 Your Account Has Been Approved!"
            
            # Email body (Plain text)
            text_body = f"""
Hello {user_name},

Great news! Your account has been approved by the administrator.

You can now login to the AI Resume Shortlisting System using your credentials.

Account Details:
- Email: {user_email}
- Status: ✅ Approved

Next Steps:
1. Visit the login page
2. Enter your email and password
3. Start using the recruitment dashboard

If you have any questions, please contact the administrator.

Thank you for your patience!

---
AI Resume Shortlisting System
Powered by AI & Machine Learning
            """
            
            # Email body (HTML)
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .info-box {{
            background: #e8f4f8;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Account Approved!</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{user_name}</strong>,</p>
            
            <p>Great news! Your account has been approved by the administrator.</p>
            
            <p>You can now login to the <strong>AI Resume Shortlisting System</strong> using your credentials.</p>
            
            <div class="info-box">
                <strong>Account Details:</strong><br>
                📧 Email: {user_email}<br>
                ✅ Status: Approved
            </div>
            
            <p><strong>Next Steps:</strong></p>
            <ol>
                <li>Visit the login page</li>
                <li>Enter your email and password</li>
                <li>Start using the recruitment dashboard</li>
            </ol>
            
            <p>If you have any questions, please contact the administrator.</p>
            
            <p>Thank you for your patience!</p>
        </div>
        <div class="footer">
            <p>AI Resume Shortlisting System</p>
            <p>Powered by AI & Machine Learning</p>
            <p>© 2025 All rights reserved</p>
        </div>
    </div>
</body>
</html>
            """
            
            # Attach both versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True, f"✅ Approval email sent to {user_email}"
        
        except Exception as e:
            return False, f"❌ Failed to send email: {str(e)}"
    
    def send_device_approval_email(self, user_email: str, user_name: str, device_id: str) -> tuple:
        """Send notification when new device is approved"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = user_email
            msg['Subject'] = "🔐 New Device Approved"
            
            text_body = f"""
Hello {user_name},

Your new device has been approved for login.

Device ID: {device_id[:8]}...

You can now login from this device using your credentials.

If you didn't request this approval, please contact the administrator immediately.

---
AI Resume Shortlisting System
            """
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .warning {{
            background: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ff9800;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 New Device Approved</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{user_name}</strong>,</p>
            
            <p>Your new device has been approved for login.</p>
            
            <p><strong>Device ID:</strong> {device_id[:8]}...</p>
            
            <p>You can now login from this device using your credentials.</p>
            
            <div class="warning">
                <strong>⚠️ Security Notice:</strong><br>
                If you didn't request this approval, please contact the administrator immediately.
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True, f"✅ Device approval email sent to {user_email}"
        
        except Exception as e:
            return False, f"❌ Failed to send email: {str(e)}"
    
    def notify_admin_new_signup(self, user_email: str, user_name: str, admin_email: str) -> tuple:
        """Notify admin about new user signup"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = admin_email
            msg['Subject'] = f"🔔 New User Signup: {user_name}"
            
            text_body = f"""
Admin Notification

A new user has signed up and is waiting for approval.

User Details:
- Name: {user_name}
- Email: {user_email}
- Signup Time: {user_email}

Please review and approve/reject this user in the admin panel.

---
AI Resume Shortlisting System
            """
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .header {{
            background: #ff6b6b;
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .user-info {{
            background: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 New User Signup</h1>
        </div>
        <div class="content">
            <p><strong>Admin Notification</strong></p>
            
            <p>A new user has signed up and is waiting for approval.</p>
            
            <div class="user-info">
                <strong>User Details:</strong><br>
                👤 Name: {user_name}<br>
                📧 Email: {user_email}
            </div>
            
            <p>Please review and approve/reject this user in the admin panel.</p>
        </div>
    </div>
</body>
</html>
            """
            
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True, f"✅ Admin notified about new signup"
        
        except Exception as e:
            return False, f"❌ Failed to notify admin: {str(e)}"