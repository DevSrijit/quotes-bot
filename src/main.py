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
        """Run the bot with scheduling"""
        try:
            if test_mode:
                logger.info("Running in test mode...")
                self.generate_and_post(test_mode=True)
                return
                
            logger.info("Starting bot in production mode...")
            self.monitoring.report_startup()
            
            scheduler = BackgroundScheduler()
            
            # Add posting job
            posting_trigger = IntervalTrigger(
                hours=24/int(os.getenv('POSTS_PER_DAY', 1)),
                jitter=1800  # 30 minutes of randomness
            )
            scheduler.add_job(
                self.generate_and_post,
                trigger=posting_trigger,
                name='post_job'
            )
            
            # Add token expiration check job - run daily at midnight IST
            scheduler.add_job(
                self.monitoring.check_token_expiration,
                trigger=CronTrigger(
                    hour=0,
                    minute=0,
                    timezone=self.ist_timezone
                ),
                name='token_check_job'
            )
            
            scheduler.start()
            logger.info("Scheduler started. Bot is running...")
            
            # Run first post immediately
            self.generate_and_post()
            
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
