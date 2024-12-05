import os
import time
import resend
from datetime import datetime
import pytz

class MonitoringService:
    def __init__(self):
        self.resend_api_key = os.getenv("RESEND_API_KEY")
        self.monitoring_email = os.getenv("MONITORING_EMAIL")
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.last_notification_time = None
        
        if not self.resend_api_key or not self.monitoring_email:
            print("Warning: RESEND_API_KEY or MONITORING_EMAIL not set. Monitoring disabled.")
            return
            
        resend.api_key = self.resend_api_key

    def _can_send_notification(self):
        """Rate limit notifications to once per hour"""
        if not self.last_notification_time:
            return True
        
        now = datetime.now(self.ist_timezone)
        time_since_last = (now - self.last_notification_time).total_seconds()
        return time_since_last > 3600  # 1 hour

    def _send_email(self, subject, content):
        if not self.resend_api_key or not self.monitoring_email:
            return
            
        if not self._can_send_notification():
            print("Skipping notification due to rate limiting")
            return
            
        try:
            now = datetime.now(self.ist_timezone).strftime("%I:%M %p IST, %d %b %Y")
            
            params = {
                "from": "Science Quotes Bot <bot@quotes.srijit.co>",
                "to": [self.monitoring_email],
                "subject": f"[Science Quotes Bot] {subject}",
                "html": f"""
                <h2>{subject}</h2>
                <p><strong>Time:</strong> {now}</p>
                <p>{content}</p>
                <hr>
                <p><em>This is an automated message from your Science Quotes Bot monitoring service.</em></p>
                """
            }
            
            resend.Emails.send(params)
            self.last_notification_time = datetime.now(self.ist_timezone)
            print(f"Sent monitoring email: {subject}")
            
        except Exception as e:
            print(f"Failed to send monitoring email: {str(e)}")

    def report_downtime(self, error_details):
        """Report service downtime or critical errors"""
        subject = "⚠️ Service Alert: Bot Encountered an Error"
        content = f"""
        The Science Quotes Bot has encountered an error and may need attention.
        
        <strong>Error Details:</strong><br>
        <pre>{error_details}</pre>
        
        <p>Please check the logs for more information.</p>
        """
        self._send_email(subject, content)

    def report_recovery(self):
        """Report service recovery after downtime"""
        subject = "✅ Service Recovery: Bot is Back Online"
        content = """
        The Science Quotes Bot has recovered and is functioning normally again.
        
        <p>The service will continue to be monitored for any further issues.</p>
        """
        self._send_email(subject, content)

    def report_startup(self):
        """Report service startup"""
        subject = "🚀 Service Started: Bot Initialized"
        content = """
        The Science Quotes Bot has been initialized and is starting up.
        
        <p>Regular operations will begin shortly.</p>
        """
        self._send_email(subject, content)
