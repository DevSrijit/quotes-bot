import os
import requests
from dotenv import load_dotenv
from pathlib import Path
import argparse
import json

def update_env_file(key: str, value: str):
    """Update a specific key in the .env file"""
    env_path = Path(__file__).parent.parent / '.env'

    # Read the current env file
    if not env_path.exists():
        with open(env_path, 'w'): pass  # Create if it doesn't exist
    with open(env_path, 'r') as f:
        lines = f.readlines()

    # Update or add the key
    key_updated = False
    for i, line in enumerate(lines):
        if line.startswith(f'{key}='):
            lines[i] = f'{key}={value}\n'
            key_updated = True
            break

    if not key_updated:
        lines.append(f'{key}={value}\n')

    # Write back to the env file
    with open(env_path, 'w') as f:
        f.writelines(lines)

    print(f"✅ Updated {key} in .env file")

def exchange_token(short_lived_token: str):
    """Exchange short-lived token for long-lived token"""
    print("Exchanging short-lived token for long-lived token...")
    app_secret = os.getenv("META_APP_SECRET")
    url = "https://graph.facebook.com/v21.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": os.getenv("META_APP_ID"),
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        long_lived_token = data.get("access_token")
        print("✅ Successfully exchanged for a long-lived token.")
        print(f"🔑 Long-lived token: {long_lived_token}")  # Print the token directly
        return long_lived_token
    else:
        raise Exception(f"Error exchanging token: {response.json()}")

def get_user_accounts(long_lived_token: str):
    """Retrieve user pages, page tokens, and Instagram Business account IDs"""
    print("Fetching user accounts and Instagram Business accounts...")
    url = "https://graph.facebook.com/v21.0/me/accounts"
    params = {
        "fields": "id,name,access_token,instagram_business_account",
        "access_token": long_lived_token
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        accounts = data.get("data", [])
        if not accounts:
            print("❌ No accounts found. Ensure the user has connected a page to their Instagram account.")
        else:
            for account in accounts:
                print(json.dumps(account, indent=4))
        return accounts
    else:
        raise Exception(f"Error fetching accounts: {response.json()}")

def refresh_long_lived_token(long_lived_token: str):
    """Refresh a long-lived token"""
    print("Refreshing long-lived token...")
    url = "https://graph.facebook.com/v21.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": os.getenv("META_APP_ID"),
        "client_secret": os.getenv("META_APP_SECRET"),
        "fb_exchange_token": long_lived_token
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        refreshed_token = data.get("access_token")
        print("✅ Successfully refreshed the long-lived token.")
        update_env_file("INSTAGRAM_ACCESS_TOKEN", refreshed_token)
        return refreshed_token
    else:
        raise Exception(f"Error refreshing token: {response.json()}")

def construct_login_url():
    """Generate the Facebook Login URL for onboarding"""
    print("Generating Facebook Login URL...")
    client_id = os.getenv("META_APP_ID")
    redirect_uri = os.getenv("REDIRECT_URI")
    scope = "instagram_basic,instagram_content_publish,instagram_manage_comments,instagram_manage_insights,pages_show_list,pages_read_engagement"
    extras = json.dumps({"setup": {"channel": "IG_API_ONBOARDING"}})

    url = (
        f"https://www.facebook.com/v21.0/dialog/oauth?"
        f"client_id={client_id}&display=page&extras={extras}&"
        f"redirect_uri={redirect_uri}&response_type=token&scope={scope}"
    )

    print(f"Login URL: {url}")
    return url

def main():
    parser = argparse.ArgumentParser(description='Instagram API Token Management')
    parser.add_argument('--exchange', help='Short-lived token to exchange for a long-lived token')
    parser.add_argument('--refresh', action='store_true', help='Refresh long-lived token')
    parser.add_argument('--login-url', action='store_true', help='Generate Facebook Login URL')
    parser.add_argument('--fetch-accounts', action='store_true', help='Fetch user accounts and Instagram Business account info')

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    if args.exchange:
        exchange_token(args.exchange)
    elif args.refresh:
        long_lived_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        if not long_lived_token:
            raise Exception("❌ INSTAGRAM_ACCESS_TOKEN is not set in .env")
        refresh_long_lived_token(long_lived_token)
    elif args.login_url:
        construct_login_url()
    elif args.fetch_accounts:
        long_lived_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        if not long_lived_token:
            raise Exception("❌ INSTAGRAM_ACCESS_TOKEN is not set in .env")
        get_user_accounts(long_lived_token)
    else:
        print("❌ Please provide an argument (--exchange, --refresh, --login-url, --fetch-accounts)")

if __name__ == "__main__":
    main()