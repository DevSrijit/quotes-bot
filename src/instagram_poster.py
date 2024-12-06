import os
import time
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.igmedia import IGMedia
from facebook_business.adobjects.instagramuser import InstagramUser
from pathlib import Path
import json
import requests

class InstagramPoster:
    def __init__(self):
        print("Initializing Instagram Graph API client...")
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.instagram_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        
        # Initialize the Facebook API
        FacebookAdsApi.init(access_token=self.access_token)
        
    def validate_credentials(self):
        """Validate that we have the necessary credentials and permissions"""
        try:
            print("Validating Instagram Business Account credentials...")
            
            # Try to get the Instagram Business Account info
            instagram_account = InstagramUser(self.instagram_account_id)
            account_info = instagram_account.api_get(fields=['username'])
            
            print(f"Successfully validated Instagram Business Account: {account_info['username']}")
            return True
            
        except Exception as e:
            print(f"Failed to validate credentials: {str(e)}")
            return False

    def post_image(self, image_path: str, caption: str) -> bool:
        try:
            print("\nStarting Instagram Graph API posting process...")
            if not self.validate_credentials():
                print("Aborting post due to credential validation failure")
                return False
            
            print(f"Uploading image from path: {image_path}")
            
            # First, we need to upload the image and get a creation ID
            with open(image_path, 'rb') as image_file:
                # Create container
                instagram_account = InstagramUser(self.instagram_account_id)
                creation = instagram_account.create_media(
                    params={
                        'image_url': image_path,
                        'caption': caption,
                        'access_token': self.access_token,
                    }
                )
                
                if 'id' not in creation:
                    raise Exception("Failed to get creation ID")
                
                creation_id = creation['id']
                
                # Publish the container
                instagram_account.create_media_publish(
                    params={
                        'creation_id': creation_id,
                        'access_token': self.access_token,
                    }
                )
            
            print(f"Successfully posted to Instagram. Creation ID: {creation_id}")
            
            # Clean up the image file
            if os.path.exists(image_path):
                print(f"Cleaning up image file: {image_path}")
                os.remove(image_path)
                
            return True
            
        except Exception as e:
            print(f"Failed to post to Instagram. Error: {str(e)}")
            return False
            
    def cleanup(self):
        """Clean up any temporary files"""
        pass  # No session files needed with Graph API
