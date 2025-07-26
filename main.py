from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Contact Form API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    company: str = ""
    subject: str
    message: str

# Email configuration
EMAIL_CONFIG = {
    "hostname": os.getenv("EMAIL_HOST", "smtp.gmail.com"),
    "port": int(os.getenv("EMAIL_PORT", "587")),
    "username": os.getenv("EMAIL_USER"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "use_tls": True,
}

RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")  # Your email to receive notifications

async def send_notification_email(form_data: ContactForm):
    """Send email notification when form is submitted"""
    
    if not all([EMAIL_CONFIG["username"], EMAIL_CONFIG["password"], RECIPIENT_EMAIL]):
        raise HTTPException(
            status_code=500, 
            detail="Email configuration is incomplete. Check your environment variables."
        )
    
    try:
        # Create the email message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"🔔 New Contact Form: {form_data.subject}"
        message["From"] = EMAIL_CONFIG["username"]
        message["To"] = RECIPIENT_EMAIL
        message["Reply-To"] = form_data.email
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #7c3aed; border-bottom: 2px solid #7c3aed; padding-bottom: 10px;">
                    📬 New Contact Form Submission
                </h2>
                
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #4a5568;">Name:</td>
                            <td style="padding: 8px 0;">{form_data.name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #4a5568;">Email:</td>
                            <td style="padding: 8px 0;"><a href="mailto:{form_data.email}">{form_data.email}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #4a5568;">Company:</td>
                            <td style="padding: 8px 0;">{form_data.company or 'Not specified'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #4a5568;">Subject:</td>
                            <td style="padding: 8px 0;"><span style="background: #7c3aed; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{form_data.subject}</span></td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2d3748;">Message:</h3>
                    <p style="white-space: pre-line; line-height: 1.6;">{form_data.message}</p>
                </div>
                
                <div style="background: #edf2f7; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
                    <p style="margin: 0; font-size: 14px; color: #4a5568;">
                        📅 Submitted on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                    </p>
                    <p style="margin: 10px 0 0 0; font-size: 14px;">
                        <a href="mailto:{form_data.email}?subject=Re: {form_data.subject}" 
                           style="background: #7c3aed; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">
                            📧 Reply to {form_data.name}
                        </a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach both versions       
        message.attach(MIMEText(html_content, "html"))
        
        # Send the email
        await aiosmtplib.send(
            message,
            hostname=EMAIL_CONFIG["hostname"],
            port=EMAIL_CONFIG["port"],
            start_tls=EMAIL_CONFIG["use_tls"],
            username=EMAIL_CONFIG["username"],
            password=EMAIL_CONFIG["password"],
        )
        
        return True
        
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

async def send_confirmation_email(form_data: ContactForm):
    """Send confirmation email to the person who submitted the form"""
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = "✅ Thanks for reaching out!"
        message["From"] = EMAIL_CONFIG["username"]
        message["To"] = form_data.email
        

        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #10b981;">✅ Thanks for reaching out, {form_data.name}!</h2>
                
                <p>I've received your message about <strong>"{form_data.subject}"</strong> and will get back to you soon.</p>
                
                <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0;">
                    <h4 style="margin-top: 0;">Your message:</h4>
                    <p style="white-space: pre-line;">{form_data.message}</p>
                </div>
                
                <p>I typically respond within <strong>24-48 hours</strong>.</p>
                
                <p>Best regards! 🚀</p>
            </div>
        </body>
        </html>
        """
        

        message.attach(MIMEText(html_content, "html"))
        
        await aiosmtplib.send(
            message,
            hostname=EMAIL_CONFIG["hostname"],
            port=EMAIL_CONFIG["port"],
            start_tls=EMAIL_CONFIG["use_tls"],
            username=EMAIL_CONFIG["username"],
            password=EMAIL_CONFIG["password"],
        )
        
        return True
        
    except Exception as e:
        print(f"Confirmation email failed: {str(e)}")
        return False

@app.post("/api/contact")
async def submit_contact_form(form_data: ContactForm):
    """Handle contact form submission - email notifications only"""
    
    try:

        notification_sent = await send_notification_email(form_data)
        
        if not notification_sent:
            raise HTTPException(
                status_code=500, 
                detail="Failed to send notification email. Please try again."
            )
        

        confirmation_sent = await send_confirmation_email(form_data)
        
        return {
            "success": True,
            "message": "Your message has been sent successfully!",
            "details": {
                "notification_sent": notification_sent,
                "confirmation_sent": confirmation_sent
            }
        }
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred. Please try again later."
        )

