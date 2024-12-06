import os
import time
import requests
from pathlib import Path
import json
import logging
import tempfile
import urllib.parse
from datetime import datetime, timezone

class InstagramPoster:
    def __init__(self):
        print("Initializing Instagram Graph API client...")
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.app_id = os.getenv("META_APP_ID")
        self.app_secret = os.getenv("META_APP_SECRET")
        self.instagram_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def exchange_token(self, short_lived_token: str = None) -> str:
        """Exchange a short-lived token for a long-lived one"""
        if not self.app_id or not self.app_secret:
            raise Exception("META_APP_ID and META_APP_SECRET environment variables are required")
        
        token_to_exchange = short_lived_token or self.access_token
        
        url = f"https://graph.facebook.com/{self.api_version}/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'fb_exchange_token': token_to_exchange
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to exchange token: {response.text}")
            
        data = response.json()
        return data.get('access_token')

    def get_token_info(self, token: str = None) -> dict:
        """Get information about an access token"""
        token_to_check = token or self.access_token
        
        url = f"https://graph.facebook.com/debug_token"
        params = {
            'input_token': token_to_check,
            'access_token': f"{self.app_id}|{self.app_secret}"
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to get token info: {response.text}")
            
        data = response.json()
        return data.get('data', {})

    def is_token_valid(self) -> bool:
        """Check if the current access token is valid and not expired"""
        try:
            token_info = self.get_token_info()
            if not token_info.get('is_valid'):
                return False
                
            # Check expiration
            expires_at = token_info.get('expires_at', 0)
            if expires_at == 0:  # Never expires
                return True
                
            now = int(time.time())
            return now < expires_at
            
        except Exception as e:
            print(f"Error checking token validity: {str(e)}")
            return False

    def upload_to_imgbb(self, image_path: str) -> str:
        """Upload image to imgbb and return the URL"""
        imgbb_key = os.getenv("IMGBB_API_KEY")
        if not imgbb_key:
            raise Exception("IMGBBB_API_KEY environment variable is required")
        
        print("Uploading image to temporary hosting...")
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = requests.post(
                'https://api.imgbb.com/1/upload',
                params={'key': imgbb_key, 'expiration': 600},
                files=files
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to upload to imgbb: {response.text}")
            
            data = response.json()
            if not data.get('success'):
                raise Exception(f"imgbb upload failed: {data}")
                
            return data['data']['url']
        
    def validate_credentials(self):
        """Validate credentials and check publishing limit"""
        try:
            print("Validating Instagram Business Account credentials...")
            
            # First check token validity
            if not self.is_token_valid():
                raise Exception("Access token is invalid or expired. Please refresh the token.")
            
            # Check account info
            url = f"{self.base_url}/{self.instagram_account_id}"
            params = {
                'fields': 'username',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise Exception(f"API validation failed: {response.text}")
                
            account_info = response.json()
            print(f"Successfully validated Instagram Business Account: {account_info.get('username')}")
            
            # Check publishing limit
            limit_url = f"{self.base_url}/{self.instagram_account_id}/content_publishing_limit"
            params = {
                'fields': 'config,quota_usage',
                'access_token': self.access_token
            }
            
            limit_response = requests.get(limit_url, params=params)
            if limit_response.status_code == 200:
                limit_data = limit_response.json().get('data', [{}])[0]
                quota_usage = limit_data.get('quota_usage', 0)
                print(f"Publishing quota usage: {quota_usage}/50 posts in last 24 hours")
                if quota_usage >= 50:
                    raise Exception("Publishing quota exceeded. Please wait.")
            
            return True
            
        except Exception as e:
            print(f"Failed to validate credentials: {str(e)}")
            return False

    def check_container_status(self, container_id):
        """Check the status of a media container"""
        url = f"{self.base_url}/{container_id}"
        params = {
            'fields': 'status_code,status',
            'access_token': self.access_token
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to check container status: {response.text}")
            
        data = response.json()
        return data.get('status_code'), data.get('status')

    def wait_for_container_ready(self, container_id, timeout=300, interval=5):
        """Wait for container to be ready for publishing"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_code, status = self.check_container_status(container_id)
            
            if status_code == 'FINISHED':
                return True
            elif status_code in ['ERROR', 'EXPIRED']:
                raise Exception(f"Container failed: {status}")
                
            print(f"Container status: {status_code} - {status}")
            time.sleep(interval)
            
        raise Exception("Timeout waiting for container to be ready")

    def post_image(self, image_path: str, caption: str) -> bool:
        try:
            print("\nStarting Instagram Graph API posting process...")
            if not self.validate_credentials():
                print("Aborting post due to credential validation failure")
                return False
            
            print(f"Creating media container for image: {image_path}")
            
            # First upload the image to a temporary hosting service
            image_url = self.upload_to_imgbb(image_path)
            print(f"Image uploaded to temporary URL: {image_url}")
            
            # Create the media container
            container_url = f"{self.base_url}/{self.instagram_account_id}/media"
            
            # Prepare the parameters
            params = {
                'image_url': image_url,
                'caption': caption,
                'access_token': self.access_token
            }
            
            # Create the container
            response = requests.post(container_url, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to create media container: {response.text}")
            
            container_data = response.json()
            if 'id' not in container_data:
                raise Exception(f"No container ID in response: {response.text}")
            
            container_id = container_data['id']
            print(f"Created container with ID: {container_id}")
            
            # Wait for container to be ready
            self.wait_for_container_ready(container_id)
            
            # Step 2: Publish the container
            publish_url = f"{self.base_url}/{self.instagram_account_id}/media_publish"
            publish_params = {
                'creation_id': container_id,
                'access_token': self.access_token
            }
            
            publish_response = requests.post(publish_url, params=publish_params)
            if publish_response.status_code != 200:
                raise Exception(f"Failed to publish media: {publish_response.text}")
            
            media_id = publish_response.json().get('id')
            print(f"Successfully published to Instagram. Media ID: {media_id}")
            
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
