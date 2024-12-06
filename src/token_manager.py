import os
from dotenv import load_dotenv
from pathlib import Path
from instagram_poster import InstagramPoster
import argparse

def update_env_file(token: str):
    """Update the INSTAGRAM_ACCESS_TOKEN in .env file"""
    env_path = Path(__file__).parent.parent / '.env'
    
    # Read current env file
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update or add the token
    token_updated = False
    for i, line in enumerate(lines):
        if line.startswith('INSTAGRAM_ACCESS_TOKEN='):
            lines[i] = f'INSTAGRAM_ACCESS_TOKEN={token}\n'
            token_updated = True
            break
    
    if not token_updated:
        lines.append(f'INSTAGRAM_ACCESS_TOKEN={token}\n')
    
    # Write back to env file
    with open(env_path, 'w') as f:
        f.writelines(lines)

def exchange_token(short_lived_token: str = None):
    """Exchange a short-lived token for a long-lived one and update .env"""
    try:
        # Initialize Instagram poster
        instagram = InstagramPoster()
        
        # Exchange token
        print("Exchanging token...")
        long_lived_token = instagram.exchange_token(short_lived_token)
        
        # Get token info
        token_info = instagram.get_token_info(long_lived_token)
        expires_at = token_info.get('expires_at', 0)
        
        if expires_at == 0:
            print("✅ Successfully obtained a never-expiring token!")
        else:
            import datetime
            expiry_date = datetime.datetime.fromtimestamp(expires_at)
            print(f"✅ Successfully obtained a long-lived token!")
            print(f"Token will expire on: {expiry_date}")
        
        # Update .env file
        print("\nUpdating .env file...")
        update_env_file(long_lived_token)
        print("✅ Updated INSTAGRAM_ACCESS_TOKEN in .env file")
        
        print("\n🎉 Token exchange complete! Your Instagram bot is ready to go.")
        
    except Exception as e:
        print(f"❌ Error exchanging token: {str(e)}")
        print("\nPlease make sure you have:")
        print("1. Added META_APP_ID and META_APP_SECRET to your .env file")
        print("2. Have a valid short-lived token")
        print("3. Have proper permissions set up in your Meta App")

def main():
    parser = argparse.ArgumentParser(description='Exchange Instagram API tokens')
    parser.add_argument('--token', help='Short-lived token to exchange. If not provided, uses token from .env')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Exchange token
    exchange_token(args.token)

if __name__ == "__main__":
    main()
