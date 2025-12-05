"""
Email service for sending SMTP emails
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        """Initialize email service with SMTP configuration from environment variables"""
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.smtp_from_email = os.environ.get('SMTP_FROM_EMAIL', self.smtp_username)
        self.smtp_from_name = os.environ.get('SMTP_FROM_NAME', 'User Story Automation')
        self.use_tls = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # Check if SMTP is configured
        self.is_configured = bool(self.smtp_username and self.smtp_password)
        
        if not self.is_configured:
            logger.warning("SMTP not configured. Email functionality will be disabled.")
            logger.warning("Set SMTP_USERNAME and SMTP_PASSWORD environment variables to enable emails.")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text email body (optional, will be generated from HTML if not provided)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning(f"SMTP not configured. Skipping email to {to_email}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((self.smtp_from_name, self.smtp_from_email))
            msg['To'] = to_email
            
            # Create plain text version if not provided
            if not body_text:
                # Simple HTML to text conversion (remove HTML tags)
                import re
                body_text = re.sub(r'<[^>]+>', '', body_html)
                body_text = body_text.replace('&nbsp;', ' ')
                body_text = body_text.replace('&amp;', '&')
                body_text = body_text.replace('&lt;', '<')
                body_text = body_text.replace('&gt;', '>')
            
            # Add both plain text and HTML versions
            part1 = MIMEText(body_text, 'plain')
            part2 = MIMEText(body_html, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """
        Send welcome email to new user
        
        Args:
            user_email: User's email address
            user_name: User's name
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Welcome to User Story Automation!"
        
        # HTML email body
        body_html = f"""
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
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to User Story Automation!</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    
                    <p>Thank you for joining User Story Automation! We're excited to have you on board.</p>
                    
                    <p>With our platform, you can:</p>
                    <ul>
                        <li>Upload requirement documents and automatically generate user stories</li>
                        <li>Extract epics, deliverables, and test cases from your documents</li>
                        <li>Export your user stories in various formats</li>
                    </ul>
                    
                    <p>Get started by uploading your first document and see how we can help streamline your requirements process.</p>
                    
                    <a href="#" class="button">Get Started</a>
                    
                    <p>If you have any questions, feel free to reach out to our support team.</p>
                    
                    <p>Best regards,<br>The User Story Automation Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body_html)


# Create a singleton instance
email_service = EmailService()

