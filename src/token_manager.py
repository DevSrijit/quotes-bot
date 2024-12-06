import os
from dotenv import load_dotenv
from pathlib import Path
import requests
import argparse

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
    url = "https://graph.instagram.com/access_token"
    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": app_secret,
        "access_token": short_lived_token
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        long_lived_token = data.get("access_token")
        expires_in = data.get("expires_in")
        print(f"✅ Long-lived token obtained! Expires in {expires_in // (24 * 60 * 60)} days.")
        update_env_file("INSTAGRAM_ACCESS_TOKEN", long_lived_token)
        return long_lived_token
    else:
        raise Exception(f"Error exchanging token: {response.json()}")

def refresh_long_lived_token(long_lived_token: str):
    """Refresh long-lived token"""
    print("Refreshing long-lived token...")
    url = "https://graph.instagram.com/refresh_access_token"
    params = {
        "grant_type": "ig_refresh_token",
        "access_token": long_lived_token
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        refreshed_token = data.get("access_token")
        expires_in = data.get("expires_in")
        print(f"✅ Long-lived token refreshed! Expires in {expires_in // (24 * 60 * 60)} days.")
        update_env_file("INSTAGRAM_ACCESS_TOKEN", refreshed_token)
        return refreshed_token
    else:
        raise Exception(f"Error refreshing token: {response.json()}")

def main():
    parser = argparse.ArgumentParser(description='Instagram API Token Management')
    parser.add_argument('--exchange', help='Short-lived token to exchange for a long-lived token')
    parser.add_argument('--refresh', action='store_true', help='Refresh long-lived token')

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    if args.exchange:
        # Exchange short-lived token
        exchange_token(args.exchange)
    elif args.refresh:
        # Refresh long-lived token
        long_lived_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        if not long_lived_token:
            raise Exception("❌ INSTAGRAM_ACCESS_TOKEN is not set in .env")
        refresh_long_lived_token(long_lived_token)
    else:
        print("❌ Please provide --exchange or --refresh argument")

if __name__ == "__main__":
    main()
