from datetime import datetime, timedelta
from typing import Dict, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from pathlib import Path
from jinja2 import Template

class InterviewScheduler:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent.parent / "templates"
        self.email_settings = {
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "sender_email": os.getenv("SENDER_EMAIL", ""),
            "sender_password": os.getenv("SENDER_PASSWORD", "")
        }
    
    def generate_time_slots(self, start_date: datetime, 
                          num_days: int = 5, 
                          slots_per_day: int = 8) -> List[datetime]:
        """Generate available interview time slots"""
        time_slots = []
        current_date = start_date
        
        for _ in range(num_days):
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
                
            # Generate slots for the day
            slot_time = current_date.replace(hour=9, minute=0)  # Start at 9 AM
            for _ in range(slots_per_day):
                time_slots.append(slot_time)
                slot_time += timedelta(minutes=60)  # 1-hour slots
                
            current_date += timedelta(days=1)
            
        return time_slots
    
    def send_interview_invitation(self, 
                                candidate_email: str,
                                candidate_name: str,
                                job_title: str,
                                company: str,
                                interview_datetime: datetime,
                                meeting_link: str = None) -> bool:
        """Send interview invitation email to candidate"""
        try:
            # Load email template
            template_path = self.template_dir / "interview_invitation.html"
            with open(template_path, "r") as f:
                template = Template(f.read())
            
            # Prepare email content
            email_content = template.render(
                candidate_name=candidate_name,
                job_title=job_title,
                company=company,
                interview_datetime=interview_datetime.strftime("%Y-%m-%d %H:%M"),
                meeting_link=meeting_link
            )
            
            # Create email message
            msg = MIMEMultipart()
            msg["Subject"] = f"Interview Invitation: {job_title} at {company}"
            msg["From"] = self.email_settings["sender_email"]
            msg["To"] = candidate_email
            
            msg.attach(MIMEText(email_content, "html"))
            
            # Send email
            with smtplib.SMTP(self.email_settings["smtp_server"], 
                            self.email_settings["smtp_port"]) as server:
                server.starttls()
                server.login(
                    self.email_settings["sender_email"],
                    self.email_settings["sender_password"]
                )
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            print(f"Error sending interview invitation: {str(e)}")
            return False
    
    def schedule_interview(self, candidate: Dict, job: Dict, 
                         interview_datetime: datetime) -> bool:
        """Schedule an interview and send invitation"""
        try:
            # Generate a mock meeting link (in real implementation, this would integrate with
            # calendar/meeting services like Google Calendar or Zoom)
            meeting_link = f"https://meet.company.com/{job['id']}-{candidate['id']}"
            
            # Send interview invitation
            success = self.send_interview_invitation(
                candidate_email=candidate["contact"]["email"],
                candidate_name=candidate["name"],
                job_title=job["title"],
                company=job["company"],
                interview_datetime=interview_datetime,
                meeting_link=meeting_link
            )
            
            return success
            
        except Exception as e:
            print(f"Error scheduling interview: {str(e)}")
            return False
