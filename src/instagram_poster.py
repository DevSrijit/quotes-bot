import os
import time
from instagrapi import Client
from pathlib import Path
from typing import Optional
import random

class InstagramPoster:
    def __init__(self):
        self.client = Client()
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.session_file = Path(os.path.dirname(os.path.dirname(__file__))) / "session.json"
        
    def login(self):
        try:
            # Try to load existing session
            if self.session_file.exists():
                self.client.load_settings(str(self.session_file))
                self.client.login(self.username, self.password)
            else:
                # Fresh login
                self.client.login(self.username, self.password)
                # Save session for future use
                self.client.dump_settings(str(self.session_file))
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def post_image(self, image_path: str, caption: str) -> bool:
        try:
            if not self.login():
                return False
                
            # Add random delay to avoid exact timing
            delay = random.randint(1, 300)  # Random delay between 1-300 seconds
            time.sleep(delay)
            
            print("Uploading to Instagram...")
            media = self.client.photo_upload(
                image_path,
                caption=caption
            )
            
            print(f"Successfully posted to Instagram. Media ID: {media.id}")
            
            # Clean up the image file
            if os.path.exists(image_path):
                os.remove(image_path)
                
            return True
            
        except Exception as e:
            print(f"Failed to post to Instagram: {e}")
            return False
            
    def cleanup(self):
        """Clean up any temporary files or sessions"""
        try:
            if self.session_file.exists():
                os.remove(self.session_file)
        except Exception as e:
            print(f"Cleanup error: {e}")
