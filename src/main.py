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

class ScienceQuotesBot:
    def __init__(self):
        print("Initializing bot...")
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
        """Generate a quote and post it to Instagram"""
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
                error_msg = "Failed to generate quote"
                print(error_msg)
                self.monitoring.report_downtime(error_msg)
                return
            print("Quote generated successfully!")
            print(f"Quote: {quote_data['quote']}")
            print(f"Author: {quote_data['author']}")
                
            # Generate image
            print("\n2. Generating image...")
            image_path = self.image_generator.create_quote_image(
                quote_data['quote'],
                quote_data['author']
            )
            if not image_path:
                error_msg = "Failed to generate image"
                print(error_msg)
                self.monitoring.report_downtime(error_msg)
                return
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
                error_msg = "Failed to post to Instagram"
                print(error_msg)
                self.monitoring.report_downtime(error_msg)
            
        except Exception as e:
            error_msg = f"Error in generate_and_post: {str(e)}"
            print(error_msg)
            import traceback
            print("Full traceback:")
            print(traceback.format_exc())
            self.monitoring.report_downtime(error_msg)
            self.error_reported = True
    
    def run(self, test_mode=False):
        if test_mode:
            print("Running in test mode...")
            self.generate_and_post(test_mode=True)
            return
        
        # Report startup
        self.monitoring.report_startup()
            
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
