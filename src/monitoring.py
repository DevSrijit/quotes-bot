import os
import resend
from datetime import datetime
import pytz

class MonitoringService:
    def __init__(self):
        self.resend_api_key = os.getenv("RESEND_API_KEY")
        self.admin_email = os.getenv("MONITORING_EMAIL")
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        resend.api_key = self.resend_api_key

    def send_alert(self, subject: str, message: str):
        """Send alert email using Resend API"""
        try:
            now = datetime.now(self.ist_timezone)
            formatted_time = now.strftime("%Y-%m-%d %I:%M %p IST")
            
            html_content = f"""
            <h2>Quotable Science Alert</h2>
            <p><strong>Time:</strong> {formatted_time}</p>
            <p><strong>Issue:</strong> {message}</p>
            """

            params = {
                "from": "Quotable Science <quoutablescience@srijit.co>",
                "to": [self.admin_email],
                "subject": f"[Alert] {subject}",
                "html": html_content,
            }

            email = resend.Emails.send(params)
            print(f"Alert email sent: {email}")
            return True
        except Exception as e:
            print(f"Failed to send alert email: {str(e)}")
            return False

    def report_downtime(self, error_message: str):
        """Report downtime to admin"""
        subject = "Account Service Downtime Detected"
        self.send_alert(subject, error_message)

    def report_recovery(self):
        """Report service recovery to admin"""
        subject = "Account Service Recovered"
        message = "The Science Quotes Account service has recovered and is running normally."
        self.send_alert(subject, message)
