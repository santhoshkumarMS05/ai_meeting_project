import smtplib
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
from groq import Groq

# Load environment variables at module level
load_dotenv()

# Initialize Groq client at module level
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds

def generate_email_content(recipient_name, meeting_summary):
    """
    Generate personalized email content using Groq AI based on meeting summary
    """
    try:
        prompt = f"""You are an AI assistant that writes professional meeting follow-up emails.

Given the following information:
- Recipient Name: {recipient_name}
- Meeting Summary: {meeting_summary[:500]}

Write a short, professional email message (3-4 lines only) that includes:
1. A personalized greeting using the recipient's name
2. A brief 1-2 line summary of the meeting
3. A professional closing line mentioning the attached PDF report

Keep it concise, professional, and friendly. Do not include subject line, signature, or any formatting. Just the email body text.

Example format:
Hi [Name],
[Brief meeting summary in 1-2 lines]
Please find attached the detailed meeting summary and action items for your reference.

Now write the email:"""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=300,
        )
        
        email_content = chat_completion.choices[0].message.content.strip()
        return email_content
    
    except Exception as e:
        print(f"Error generating email content with AI: {e}")
        # Fallback to template if AI fails
        return f"""Hi {recipient_name},

Please find attached the meeting summary and assigned action items discussed today.

Kindly review the attached PDF report for detailed information.

Thanks."""


def send_email_with_pdf(recipient_name, recipient_email, pdf_path, meeting_summary, meeting_title):
    """
    Send email with PDF attachment to the recipient with retry logic.
    
    Args:
        recipient_name: Name of the recipient
        recipient_email: Email address of the recipient
        pdf_path: Path to the PDF file
        meeting_summary: Summary of the meeting for email content generation
        meeting_title: Title of the meeting for email subject
    
    Returns:
        tuple: (success: bool, message: str)
    """
    
    # Sender email configuration
    sender_email = "mugiwarayaluffy185@gmail.com"
    sender_password = os.getenv("EMAIL_APP_PASSWORD")  # Gmail App Password
    
    if not sender_password:
        print("Error: Email app password not configured in .env file")
        return False, "Email app password not configured in .env file"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return False, f"PDF file not found at {pdf_path}"
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            print(f"📧 Sending email to {recipient_email} (Attempt {attempt + 1}/{MAX_RETRIES + 1})")
            
            # Generate AI-powered email content
            email_body = generate_email_content(recipient_name, meeting_summary)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"Meeting Agent <{sender_email}>"
            msg['To'] = recipient_email
            msg['Subject'] = f"Meeting Summary: {meeting_title}"
            
            # Add body to email
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Attach PDF
            with open(pdf_path, 'rb') as f:
                pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                pdf_filename = os.path.basename(pdf_path)
                pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
                msg.attach(pdf_attachment)
            
            # Connect to Gmail SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            
            # Login to email account
            server.login(sender_email, sender_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully to {recipient_email}")
            return True, f"Email sent successfully to {recipient_email}"
        
        except smtplib.SMTPAuthenticationError:
            error_msg = "Authentication failed. Please check your email app password in .env file"
            print(f"❌ {error_msg}")
            return False, error_msg
        
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Retry if not the last attempt
            if attempt < MAX_RETRIES:
                print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                return False, error_msg
        
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Retry if not the last attempt
            if attempt < MAX_RETRIES:
                print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                return False, error_msg
    
    return False, "Failed to send email after retries"


def send_emails_to_multiple_recipients(recipients, pdf_path, meeting_summary, meeting_title):
    """
    Send emails to multiple recipients with retry logic
    
    Args:
        recipients: List of dictionaries with 'name' and 'email' keys
        pdf_path: Path to the PDF file
        meeting_summary: Summary of the meeting
        meeting_title: Title of the meeting
    
    Returns:
        dict: Results for each recipient
    """
    results = {}
    
    for recipient in recipients:
        name = recipient.get('name', '')
        email = recipient.get('email', '')
        
        if not name or not email:
            results[email or 'unknown'] = {
                'success': False,
                'message': 'Missing name or email'
            }
            continue
        
        success, message = send_email_with_pdf(
            name, 
            email, 
            pdf_path, 
            meeting_summary, 
            meeting_title
        )
        
        results[email] = {
            'success': success,
            'message': message,
            'name': name
        }
    
    return results