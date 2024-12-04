import os
import time
from instagrapi import Client
from pathlib import Path

class InstagramPoster:
    def __init__(self):
        print("Initializing Instagram client...")
        self.client = Client()
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.session_file = Path(os.path.dirname(os.path.dirname(__file__))) / "session.json"
        
    def login(self):
        try:
            print(f"Attempting Instagram login for user: {self.username}")
            
            if self.session_file.exists():
                print("Found existing session, attempting to load...")
                try:
                    self.client.load_settings(str(self.session_file))
                    # Verify session is still valid with a simple API call
                    self.client.get_timeline_feed()
                    print("Existing session is valid!")
                    return True
                except Exception as e:
                    print(f"Existing session invalid: {str(e)}")
                    print("Will attempt fresh login...")
                    os.remove(self.session_file)
            
            # Only reach here if no session exists or it was invalid
            print("Performing fresh login...")
            self.client.login(self.username, self.password)
            print("Login successful!")
            
            # Save session for future use
            self.client.dump_settings(str(self.session_file))
            print("Session saved for future use")
            return True
            
        except Exception as e:
            print(f"Login failed with error: {str(e)}")
            if self.session_file.exists():
                print("Removing failed session file...")
                os.remove(self.session_file)
            return False

    def post_image(self, image_path: str, caption: str) -> bool:
        try:
            print("\nStarting Instagram posting process...")
            if not self.login():
                print("Aborting post due to login failure")
                return False
                
            print(f"Uploading image from path: {image_path}")
            media = self.client.photo_upload(
                image_path,
                caption=caption
            )
            
            print(f"Successfully posted to Instagram. Media ID: {media.id}")
            
            # Clean up the image file
            if os.path.exists(image_path):
                print(f"Cleaning up image file: {image_path}")
                os.remove(image_path)
                
            return True
            
        except Exception as e:
            print(f"Failed to post to Instagram. Error: {str(e)}")
            if "login_required" in str(e).lower():
                print("Login error detected, removing session file...")
                if self.session_file.exists():
                    os.remove(self.session_file)
            return False
            
    def cleanup(self):
        """Clean up any temporary files or sessions"""
        try:
            if self.session_file.exists():
                print("Cleaning up session file...")
                os.remove(self.session_file)
        except Exception as e:
            print(f"Cleanup error: {e}")
