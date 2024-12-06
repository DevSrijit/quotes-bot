import os
import time
import resend
from datetime import datetime, timedelta
import pytz
from token_manager import refresh_long_lived_token

class MonitoringService:
    def __init__(self):
        self.resend_api_key = os.getenv("RESEND_API_KEY")
        self.monitoring_email = os.getenv("MONITORING_EMAIL")
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.last_notification_time = None
        self.token_creation_date = datetime(2023, 12, 6, tzinfo=self.ist_timezone)  # Token created on Dec 6, 2023
        
        if not self.resend_api_key or not self.monitoring_email:
            print("Warning: RESEND_API_KEY or MONITORING_EMAIL not set. Monitoring disabled.")
            return
            
        resend.api_key = self.resend_api_key
        
        # Check token expiration on startup
        self.check_token_expiration()

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
                "from": "Quotable Science <quotes@srijit.co>",
                "to": [self.monitoring_email],
                "subject": f"[Quotable Science] {subject}",
                "html": f"""
                <h2>{subject}</h2>
                <p><strong>Time:</strong> {now}</p>
                <p>{content}</p>
                <hr>
                <p><em>This is an automated message from your monitoring service.</em></p>
                """
            }
            
            resend.Emails.send(params)
            self.last_notification_time = datetime.now(self.ist_timezone)
            print(f"Sent monitoring email: {subject}")
            
        except Exception as e:
            print(f"Failed to send monitoring email: {str(e)}")

    def check_token_expiration(self):
        """Check if the Instagram Graph API token is nearing expiration and refresh if needed"""
        now = datetime.now(self.ist_timezone)
        token_expiry = self.token_creation_date + timedelta(days=60)  # Tokens expire after 60 days
        days_until_expiry = (token_expiry - now).days
        
        # Refresh token when 7 or fewer days remain
        if 0 <= days_until_expiry <= 7:
            try:
                # Get current token from env
                current_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
                if not current_token:
                    raise Exception("INSTAGRAM_ACCESS_TOKEN not found in environment")
                
                # Attempt to refresh the token
                refreshed_token = refresh_long_lived_token(current_token)
                if refreshed_token:
                    # Update token creation date to today
                    self.token_creation_date = now
                    
                    subject = "✅ Instagram Token Refreshed Successfully"
                    content = f"""
                    Your Instagram Graph API token has been automatically refreshed.
                    
                    <strong>Token Details:</strong><br>
                    Previous Creation Date: {token_expiry.strftime('%d %B %Y')}<br>
                    New Creation Date: {now.strftime('%d %B %Y')}<br>
                    New Expiry Date: {(now + timedelta(days=60)).strftime('%d %B %Y')}
                    """
                    self._send_email(subject, content)
                    
            except Exception as e:
                # If automatic refresh fails, send an alert email
                subject = "⚠️ Instagram Token Refresh Failed"
                content = f"""
                Failed to automatically refresh your Instagram Graph API token!
                
                <strong>Error Details:</strong><br>
                <pre>{str(e)}</pre>
                
                <strong>Token Details:</strong><br>
                Creation Date: {self.token_creation_date.strftime('%d %B %Y')}<br>
                Expiry Date: {token_expiry.strftime('%d %B %Y')}<br>
                Days Remaining: {days_until_expiry}
                
                <p>Please manually generate a new long-lived access token before expiration to ensure uninterrupted service.</p>
                """
                self._send_email(subject, content)
        else:
            # Only send alert if within 7 days of expiry and days are positive
            if 0 <= days_until_expiry <= 7:  # Alert when 7 or fewer days remain
                subject = "🔑 Instagram Token Expiration Alert"
                content = f"""
                Your Instagram Graph API token will expire in {days_until_expiry} days!
                
                <strong>Token Details:</strong><br>
                Creation Date: {self.token_creation_date.strftime('%d %B %Y')}<br>
                Expiry Date: {token_expiry.strftime('%d %B %Y')}<br>
                Days Remaining: {days_until_expiry}
                
                <p>Please generate a new long-lived access token before expiration to ensure uninterrupted service.</p>
                """
                self._send_email(subject, content)

    def report_downtime(self, error_details):
        """Report service downtime or critical errors"""
        subject = "⚠️ Service Alert: Automation Encountered an Error"
        content = f"""
        The automation has encountered an error and may need attention.
        
        <strong>Error Details:</strong><br>
        <pre>{error_details}</pre>
        
        <p>Please check the logs for more information.</p>
        """
        self._send_email(subject, content)

    def report_recovery(self):
        """Report service recovery after downtime"""
        subject = "✅ Service Recovery: Automation is Back Online"
        content = """
        The automation has recovered and is functioning normally again.
        
        <p>The automation will continue to be monitored for any further issues.</p>
        """
        self._send_email(subject, content)

    def report_startup(self):
        """Report service startup"""
        subject = "🚀 Service Started: Automation Initialized"
        content = """
        The automation has been initialized and is starting up.
        
        <p>Regular operations will begin shortly.</p>
        """
        self._send_email(subject, content)
        
        # Check token expiration on startup
        self.check_token_expiration()
