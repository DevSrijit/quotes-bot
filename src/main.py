import os
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import random
from dotenv import load_dotenv

from quote_generator import QuoteGenerator
from image_generator import ImageGenerator
from instagram_poster import InstagramPoster

class ScienceQuotesBot:
    def __init__(self, posts_per_day: int = 1):
        load_dotenv()
        self.posts_per_day = posts_per_day
        self.quote_gen = QuoteGenerator()
        self.image_gen = ImageGenerator()
        self.insta = InstagramPoster()
        self.scheduler = BlockingScheduler()
        
    def create_and_post(self):
        try:
            # Generate quote
            quote_data = self.quote_gen.get_quote()
            if not quote_data:
                print("Failed to generate quote")
                return
                
            # Create image
            image_path = self.image_gen.create_quote_image(
                quote_data['quote'], 
                quote_data['author']
            )
            
            # Post to Instagram
            success = self.insta.post_image(
                image_path,
                quote_data['instagram_description']
            )
            
            # Cleanup
            if os.path.exists(image_path):
                os.remove(image_path)
                
            print(f"Post {'successful' if success else 'failed'} at {datetime.now()}")
            
        except Exception as e:
            print(f"Error in create_and_post: {e}")
    
    def schedule_posts(self):
        # Calculate time intervals
        day_start = 9  # 9 AM
        day_end = 21   # 9 PM
        posting_hours = day_end - day_start
        interval = posting_hours / self.posts_per_day
        
        # Schedule posts throughout the day
        for i in range(self.posts_per_day):
            # Calculate base hour for this post
            base_hour = day_start + (i * interval)
            
            # Add random variation (±30 minutes)
            random_minutes = random.randint(-30, 30)
            
            # Create cron trigger
            hour = int(base_hour)
            minute = random.randint(0, 59)
            
            # Adjust for random variation
            if random_minutes != 0:
                target_time = datetime.now().replace(
                    hour=hour, 
                    minute=minute
                ) + timedelta(minutes=random_minutes)
                hour = target_time.hour
                minute = target_time.minute
            
            # Add job to scheduler
            self.scheduler.add_job(
                self.create_and_post,
                CronTrigger(
                    hour=hour,
                    minute=minute
                )
            )
            
            print(f"Scheduled post {i+1}/{self.posts_per_day} for {hour:02d}:{minute:02d}")
    
    def run(self):
        self.schedule_posts()
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("Shutting down...")
            self.insta.cleanup()

if __name__ == "__main__":
    posts_per_day = int(os.getenv("POSTS_PER_DAY", "1"))
    bot = ScienceQuotesBot(posts_per_day=posts_per_day)
    bot.run()
