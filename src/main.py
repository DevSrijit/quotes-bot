import os
import random
import time
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from quote_generator import QuoteGenerator
from image_generator import ImageGenerator
from instagram_poster import InstagramPoster
from monitoring import MonitoringService
from health import run_health_server
import threading

class ScienceQuotesBot:
    def __init__(self):
        print("\nInitializing Science Quotes Bot...")
        load_dotenv()
        self.quote_generator = QuoteGenerator()
        self.image_generator = ImageGenerator()
        self.instagram_poster = InstagramPoster()
        self.monitoring = MonitoringService()
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.last_error_time = None
        self.error_reported = False
        print("Initialization complete.")
        
    def generate_and_post(self, test_mode=False):
        try:
            # Get current time in IST
            now = datetime.now(self.ist_timezone)
            
            if test_mode:
                print("\nRunning test post at", now.strftime('%I:%M %p IST'))
            else:
                # Only check posting hours in non-test mode
                if now.hour < 9 or now.hour >= 23:
                    print(f"Outside posting hours (current time: {now.strftime('%I:%M %p IST')})")
                    return
                print(f"\nStarting post generation at {now.strftime('%I:%M %p IST')}")
            
            # Generate quote
            print("\n1. Generating quote...")
            quote_data = self.quote_generator.get_quote()
            if not quote_data:
                raise Exception("Failed to generate quote")
            print("Quote generated successfully!")
            print(f"Quote: {quote_data['quote']}")
            print(f"Author: {quote_data['author']}")
                
            # Generate image
            print("\n2. Generating image...")
            image_path = self.image_generator.create_quote_image(
                quote_data['quote'],
                quote_data['author']
            )
            print(f"Image generated successfully at: {image_path}")
            
            # Post to Instagram
            print("\n3. Posting to Instagram...")
            success = self.instagram_poster.post_image(
                image_path,
                quote_data['instagram_description']
            )
            
            if success:
                print(f"\nPost completed successfully at {now.strftime('%I:%M %p IST')}")
                if self.error_reported:
                    self.monitoring.report_recovery()
                    self.error_reported = False
            else:
                raise Exception("Failed to post to Instagram")
            
        except Exception as e:
            error_msg = f"Error in generate_and_post: {str(e)}"
            print(error_msg)
            
            # Only report errors if they occur more than 30 minutes apart
            current_time = datetime.now(self.ist_timezone)
            if (not self.last_error_time or 
                (current_time - self.last_error_time).total_seconds() > 1800):
                self.monitoring.report_downtime(error_msg)
                self.last_error_time = current_time
                self.error_reported = True
    
    def run(self, test_mode=False):
        if test_mode:
            print("Running in test mode...")
            self.generate_and_post(test_mode=True)
            return
            
        # Start health check server in a separate thread
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        # Calculate posting interval
        posts_per_day = int(os.getenv("POSTS_PER_DAY", "1"))
        seconds_per_day = 14 * 3600  # 14 hours (9 AM to 11 PM)
        interval_seconds = seconds_per_day / posts_per_day
        
        # Add some randomness to interval (±30 minutes)
        random_offset = random.randint(-1800, 1800)
        interval_seconds += random_offset
        
        # Create scheduler with IST timezone
        scheduler = BackgroundScheduler(timezone=self.ist_timezone)
        
        # Schedule first post at next 9 AM IST if current time is outside posting hours
        now = datetime.now(self.ist_timezone)
        if now.hour < 9:
            # Schedule for today 9 AM
            start_date = now.replace(hour=9, minute=0, second=0, microsecond=0)
        elif now.hour >= 23:
            # Schedule for tomorrow 9 AM
            start_date = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            # Schedule immediately
            start_date = now
            
        print(f"Bot started. First post scheduled for: {start_date.strftime('%I:%M %p IST')}")
        print(f"Posting interval: {interval_seconds/3600:.2f} hours")
        
        # Add job with IST timezone
        scheduler.add_job(
            self.generate_and_post,
            IntervalTrigger(
                seconds=int(interval_seconds),
                start_date=start_date,
                timezone=self.ist_timezone
            )
        )
        
        scheduler.start()
        
        try:
            # Keep the script running
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()

if __name__ == "__main__":
    import sys
    bot = ScienceQuotesBot()
    test_mode = "--test" in sys.argv
    bot.run(test_mode)
