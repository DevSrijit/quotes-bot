from instabot import Bot
import os
from typing import Optional
import time
import random

class InstagramPoster:
    def __init__(self):
        self.bot = Bot()
        self._login()
        
    def _login(self):
        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")
        
        if not username or not password:
            raise ValueError("Instagram credentials not found in environment variables")
            
        self.bot.login(username=username, password=password)
        
    def post_image(self, image_path: str, caption: str) -> bool:
        try:
            # Add random delay to avoid exact timing
            delay = random.randint(1, 300)  # Random delay between 1-300 seconds
            time.sleep(delay)
            
            # Post to Instagram
            success = self.bot.upload_photo(image_path, caption=caption)
            
            # Clean up temporary files created by instabot
            if os.path.exists(image_path + ".REMOVE_ME"):
                os.remove(image_path + ".REMOVE_ME")
                
            return success
        except Exception as e:
            print(f"Error posting to Instagram: {e}")
            return False
        
    def cleanup(self):
        self.bot.logout()
