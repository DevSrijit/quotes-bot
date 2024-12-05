import os
import random
import time
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from quote_generator import QuoteGenerator
from image_generator import ImageGenerator
from instagram_poster import InstagramPoster
from monitoring import MonitoringService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ScienceQuotesBot')

class ScienceQuotesBot:
    def __init__(self):
        logger.info("Initializing bot...")
        load_dotenv()
        self.quote_generator = QuoteGenerator()
        self.image_generator = ImageGenerator()
        self.instagram_poster = InstagramPoster()
        self.monitoring = MonitoringService()
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.last_error_time = None
        self.error_reported = False
        logger.info("Initialization complete.")
        
    def generate_and_post(self, test_mode=False):
        """Generate a quote and post it to Instagram"""
        try:
            # Get current time in IST
            now = datetime.now(self.ist_timezone)
            
            if test_mode:
                logger.info("\nRunning test post at %s", now.strftime('%I:%M %p IST'))
            else:
                # Only check posting hours in non-test mode
                if now.hour < 9 or now.hour >= 23:
                    logger.info(f"Outside posting hours (current time: {now.strftime('%I:%M %p IST')})")
                    return
                logger.info(f"\nStarting post generation at {now.strftime('%I:%M %p IST')}")
            
            # Generate quote
            logger.info("\n1. Generating quote...")
            quote_data = self.quote_generator.get_quote()
            if not quote_data:
                error_msg = "Failed to generate quote"
                logger.error(error_msg)
                self.monitoring.report_downtime(error_msg)
                return
            logger.info("Quote generated successfully!")
            logger.info(f"Quote: {quote_data['quote']}")
            logger.info(f"Author: {quote_data['author']}")
                
            # Generate image
            logger.info("\n2. Generating image...")
            image_path = self.image_generator.create_quote_image(
                quote_data['quote'],
                quote_data['author']
            )
            if not image_path:
                error_msg = "Failed to generate image"
                logger.error(error_msg)
                self.monitoring.report_downtime(error_msg)
                return
            logger.info(f"Image generated successfully at: {image_path}")
            
            # Post to Instagram
            logger.info("\n3. Posting to Instagram...")
            success = self.instagram_poster.post_image(
                image_path,
                quote_data['instagram_description']
            )
            
            if success:
                logger.info(f"\nPost completed successfully at {now.strftime('%I:%M %p IST')}")
                if self.error_reported:
                    self.monitoring.report_recovery()
                    self.error_reported = False
            else:
                error_msg = "Failed to post to Instagram"
                logger.error(error_msg)
                self.monitoring.report_downtime(error_msg)
            
        except Exception as e:
            error_msg = f"Error in generate_and_post: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            self.monitoring.report_downtime(error_msg)
            self.error_reported = True
    
    def run(self, test_mode=False):
        if test_mode:
            logger.info("Running in test mode...")
            self.generate_and_post(test_mode=True)
            return
        
        # Report startup
        self.monitoring.report_startup()
            
        # Create scheduler with IST timezone
        scheduler = BackgroundScheduler(timezone=self.ist_timezone)
        
        # Calculate first post time
        now = datetime.now(self.ist_timezone)
        start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)  # 9 AM IST
        end_time = now.replace(hour=23, minute=0, second=0, microsecond=0)   # 11 PM IST
        
        # Calculate posting interval for regular schedule
        posts_per_day = int(os.getenv("POSTS_PER_DAY", "1"))
        active_hours = 14  # 9 AM to 11 PM
        seconds_per_day = active_hours * 3600
        interval_seconds = seconds_per_day / (posts_per_day - 1) if posts_per_day > 1 else seconds_per_day
        
        # Add randomness to interval (±15 minutes) for regular scheduling
        regular_interval = interval_seconds + random.randint(-900, 900)
        
        # If current time is within posting hours (9 AM to 11 PM)
        if now.hour >= 9 and now.hour < 23:
            # If we have at least 1 hour before end time, schedule next post
            time_until_end = (end_time - now).total_seconds()
            if time_until_end >= 3600:  # At least 1 hour remaining
                start_date = now + timedelta(minutes=random.randint(5, 15))  # Start in 5-15 minutes
                logger.info("Service restarted during active hours. Scheduling next post soon.")
                
                # Schedule the immediate post
                scheduler.add_job(
                    self.generate_and_post,
                    'date',
                    run_date=start_date,
                    timezone=self.ist_timezone
                )
                
                # Schedule regular posts starting tomorrow
                next_start = start_time + timedelta(days=1)
                trigger = IntervalTrigger(
                    seconds=regular_interval,
                    start_date=next_start,
                    timezone=self.ist_timezone
                )
            else:
                # Less than 1 hour remaining, schedule for tomorrow
                start_date = start_time + timedelta(days=1)
                logger.info("Too close to end time. Scheduling for tomorrow at 9 AM.")
                trigger = IntervalTrigger(
                    seconds=regular_interval,
                    start_date=start_date,
                    timezone=self.ist_timezone
                )
        else:
            # Outside posting hours, schedule for next 9 AM
            if now.hour < 9:
                start_date = start_time  # Today at 9 AM
            else:
                start_date = start_time + timedelta(days=1)  # Tomorrow at 9 AM
            
            trigger = IntervalTrigger(
                seconds=regular_interval,
                start_date=start_date,
                timezone=self.ist_timezone
            )
        
        # Add the regular interval job (if we haven't already added an immediate post)
        if time_until_end < 3600 or now.hour < 9 or now.hour >= 23:
            scheduler.add_job(
                self.generate_and_post,
                trigger,
                timezone=self.ist_timezone
            )
        
        logger.info(f"Bot started. First post scheduled for: {start_date.strftime('%I:%M %p IST')}")
        logger.info(f"Regular posting interval: {regular_interval/3600:.2f} hours (base interval: {interval_seconds/3600:.2f} hours)")
        
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
