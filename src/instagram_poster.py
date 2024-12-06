import os
import time
import requests
from pathlib import Path
import json
import base64

class InstagramPoster:
    def __init__(self):
        print("Initializing Instagram Graph API client...")
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
    def validate_credentials(self):
        """Validate credentials and check publishing limit"""
        try:
            print("Validating Instagram Business Account credentials...")
            
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
            
            # Step 1: Create the media container
            container_url = f"{self.base_url}/{self.instagram_account_id}/media"
            
            # Convert image to base64 for direct upload
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                
                params = {
                    'access_token': self.access_token,
                    'image_url': f"data:image/jpeg;base64,{image_data}",
                    'caption': caption
                }
                
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
