import os
import random
import time
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
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
                if now.hour < 9 or now.hour >= 3:
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
    
    def calculate_posts_for_remaining_time(self, current_hour, posts_per_day, active_start, active_end):
        """Calculate how many posts to make in remaining time of the day"""
        # Handle cross-day schedule (9 AM to 3 AM next day)
        if active_end < active_start:  # e.g., end at 3 (next day) vs start at 9
            if current_hour >= active_start:  # After start (9 AM onwards)
                remaining_hours = (24 - current_hour) + active_end
            elif current_hour < active_end:  # Early hours next day (before 3 AM)
                remaining_hours = active_end - current_hour
            else:  # Between end and start (3 AM to 9 AM)
                return 0
        else:
            if current_hour >= active_end or current_hour < active_start:
                return 0
            remaining_hours = active_end - current_hour
            
        total_active_hours = (24 - active_start + active_end) if active_end < active_start else (active_end - active_start)
        
        # Calculate posts proportionally to remaining time
        remaining_posts = int((remaining_hours / total_active_hours) * posts_per_day)
        return remaining_posts

    def schedule_day_posts(self, scheduler, start_hour, end_hour, num_posts, is_today=False):
        """Schedule posts for a specific day period"""
        if num_posts == 0:
            return
            
        # Handle cross-day schedule
        total_hours = (24 - start_hour + end_hour) if end_hour < start_hour else (end_hour - start_hour)
        interval_hours = total_hours / num_posts
        
        for i in range(num_posts):
            # Calculate base hour for this post
            raw_hour = start_hour + (i * interval_hours)
            # Adjust hour if it goes past midnight
            post_hour = raw_hour if raw_hour < 24 else (raw_hour - 24)
            
            # For today's posts, skip if the calculated hour has already passed
            if is_today:
                current_hour = datetime.now(self.ist_timezone).hour
                if post_hour <= current_hour and (post_hour > end_hour or current_hour < end_hour):
                    continue
                
            # Add the job with a cron schedule
            scheduler.add_job(
                self.generate_and_post,
                trigger=CronTrigger(
                    hour=int(post_hour),
                    minute=random.randint(0, 59),  # Random minute for each post
                    timezone=self.ist_timezone
                ),
                name=f'post_job_{i}'
            )
            logger.info(f"Scheduled post {i+1}/{num_posts} at approximately {int(post_hour):02d}:XX IST")

    def run(self, test_mode=False):
        """Run the bot with scheduling"""
        try:
            if test_mode:
                logger.info("Running in test mode...")
                self.generate_and_post(test_mode=True)
                return
                
            logger.info("Starting bot in production mode...")
            self.monitoring.report_startup()
            
            scheduler = BackgroundScheduler()
            posts_per_day = int(os.getenv('POSTS_PER_DAY', 1))
            active_hours_start = 18  # 6 PM IST
            active_hours_end = 2   # 2 AM IST (next day)
            
            # Get current time in IST
            now = datetime.now(self.ist_timezone)
            current_hour = now.hour
            
            # Handle today's remaining posts
            remaining_posts = self.calculate_posts_for_remaining_time(
                current_hour, posts_per_day, active_hours_start, active_hours_end
            )
            
            if remaining_posts > 0:
                logger.info(f"Scheduling {remaining_posts} posts for remaining time today")
                self.schedule_day_posts(
                    scheduler, 
                    max(current_hour + 1, active_hours_start), 
                    active_hours_end, 
                    remaining_posts,
                    is_today=True
                )
            
            # Schedule regular posts for subsequent days
            logger.info(f"Setting up regular schedule with {posts_per_day} posts per day")
            self.schedule_day_posts(
                scheduler,
                active_hours_start,
                active_hours_end,
                posts_per_day
            )
            
            # Add token expiration check job - run daily at 8:30 AM IST (before posting starts)
            scheduler.add_job(
                self.monitoring.check_token_expiration,
                trigger=CronTrigger(
                    hour=8,
                    minute=30,
                    timezone=self.ist_timezone
                ),
                name='token_check_job'
            )
            
            scheduler.start()
            logger.info("Scheduler started. Bot is running...")
            
            # Keep the script running
            try:
                while True:
                    time.sleep(60)
            except (KeyboardInterrupt, SystemExit):
                scheduler.shutdown()
                logger.info("Bot stopped by user")
                
        except Exception as e:
            error_msg = f"Error in run: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            self.monitoring.report_downtime(error_msg)
    
if __name__ == "__main__":
    import sys
    bot = ScienceQuotesBot()
    test_mode = "--test" in sys.argv
    bot.run(test_mode)
