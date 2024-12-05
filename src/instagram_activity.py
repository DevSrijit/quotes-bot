import os
import time
import random
from typing import List
from datetime import datetime
from instagrapi import Client
from pathlib import Path

class InstagramActivity:
    def __init__(self, client: Client = None):
        """Initialize with an existing client or create new one"""
        self.client = client if client else Client()
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.session_file = Path(os.path.dirname(os.path.dirname(__file__))) / "session.json"
        
        # Randomize daily limits based on day of week
        # Weekends have slightly different patterns than weekdays
        self.randomize_daily_limits()
        
        # Hashtags to target (will randomly select a subset each day)
        self.master_hashtags = [
            'science', 'physics', 'chemistry', 'biology', 'astronomy',
            'sciencequotes', 'scientificmethod', 'stem', 'research',
            'innovation', 'technology', 'engineering', 'mathematics',
            'quantumphysics', 'space', 'biotech', 'artificialintelligence',
            'datascience', 'computerscience', 'coding', 'machinelearning'
        ]
        # Daily subset of hashtags
        self.target_hashtags = self.get_daily_hashtags()
        
    def randomize_daily_limits(self):
        """Randomize daily limits based on time of day and day of week"""
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        
        # Base ranges for likes (different for weekdays and weekends)
        if is_weekend:
            base_likes = random.randint(35, 45)  # More active on weekends
        else:
            base_likes = random.randint(25, 35)  # Less active on weekdays
            
        # Adjust based on time of day
        hour = now.hour
        if 9 <= hour <= 11:  # Morning
            base_likes = int(base_likes * random.uniform(0.8, 1.0))
        elif 12 <= hour <= 14:  # Lunch time
            base_likes = int(base_likes * random.uniform(1.0, 1.2))
        elif 15 <= hour <= 18:  # Afternoon
            base_likes = int(base_likes * random.uniform(0.9, 1.1))
        elif 19 <= hour <= 22:  # Evening
            base_likes = int(base_likes * random.uniform(1.1, 1.3))
        else:  # Late night/early morning
            base_likes = int(base_likes * random.uniform(0.6, 0.8))
            
        self.MAX_LIKES = base_likes
        
        # Randomize timing variables
        self.MIN_ACTION_DELAY = random.randint(30, 60)
        self.MAX_ACTION_DELAY = random.randint(90, 150)
        
    def get_daily_hashtags(self) -> List[str]:
        """Get a random subset of hashtags for the day"""
        num_hashtags = random.randint(8, 12)
        return random.sample(self.master_hashtags, num_hashtags)
        
    def random_delay(self):
        """Add random delay with some natural variation"""
        base_delay = random.uniform(self.MIN_ACTION_DELAY, self.MAX_ACTION_DELAY)
        
        # Sometimes add extra delay (10% chance)
        if random.random() < 0.1:
            base_delay *= random.uniform(1.5, 2.0)
            print("Taking a slightly longer break...")
            
        # Add micro-variations
        micro_delay = random.uniform(0.1, 2.0)
        total_delay = base_delay + micro_delay
        
        time.sleep(total_delay)
    
    def get_hashtag_medias(self, hashtag: str, amount: int = None) -> List:
        """Get recent media from a hashtag with random amount"""
        if amount is None:
            amount = random.randint(7, 13)  # Randomize the amount each time
            
        try:
            medias = self.client.hashtag_medias_recent(hashtag, amount)
            return medias
        except Exception as e:
            print(f"Error fetching hashtag medias: {str(e)}")
            return []
    
    def like_media(self, media_id: str) -> bool:
        """Like a media with random delay and success rate"""
        try:
            # Simulate occasional network issues or skips (5% chance)
            if random.random() < 0.05:
                print("Temporarily skipping this post...")
                return False
                
            self.random_delay()
            self.client.media_like(media_id)
            
            # Sometimes take an extra break after liking (15% chance)
            if random.random() < 0.15:
                extra_delay = random.uniform(10, 30)
                time.sleep(extra_delay)
                
            return True
        except Exception as e:
            print(f"Error liking media: {str(e)}")
            return False
    
    def perform_daily_activity(self):
        """Perform a day's worth of organic activity (likes only)"""
        print("\nStarting daily Instagram activity...")
        
        # Randomize limits for this session
        self.randomize_daily_limits()
        print(f"Today's like limit: {self.MAX_LIKES}")
        
        # Initialize counter
        likes_count = 0
        
        # Randomize number of hashtag exploration rounds
        num_rounds = random.randint(2, 4)
        
        # Get medias from random hashtags
        for _ in range(num_rounds):
            # Take a longer break between hashtags
            if _ > 0:
                break_time = random.uniform(180, 300)  # 3-5 minutes
                print(f"\nTaking a {int(break_time/60)} minute break between hashtags...")
                time.sleep(break_time)
            
            hashtag = random.choice(self.target_hashtags)
            print(f"\nExploring #{hashtag}...")
            
            # Randomize amount of media to fetch
            fetch_amount = random.randint(7, 13)
            medias = self.get_hashtag_medias(hashtag, amount=fetch_amount)
            
            if not medias:
                continue
                
            for media in medias:
                # Break if we've hit our daily limit
                if likes_count >= self.MAX_LIKES:
                    break
                    
                # Randomize like probability for each post
                like_probability = random.uniform(0.4, 0.6)
                if random.random() < like_probability and likes_count < self.MAX_LIKES:
                    if self.like_media(media.id):
                        likes_count += 1
                        print(f"Liked post ({likes_count}/{self.MAX_LIKES})")
                
                # Randomized delay between media interactions
                interaction_delay = random.uniform(60, 240)  # 1-4 minutes
                time.sleep(interaction_delay)
        
        print("\nDaily activity completed!")
        print(f"Likes: {likes_count}/{self.MAX_LIKES}")
