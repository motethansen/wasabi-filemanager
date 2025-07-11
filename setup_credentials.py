#!/usr/bin/env python3
"""
Setup script to configure Wasabi credentials for the File Manager
"""

import json
import keyring
import getpass
import sys
import os

# Constants
CONFIG_FILE = 'app_config.json'
SERVICE_NAME = 'WasabiFileManager'

def store_credential(profile_name, access_key, secret_key):
    """Store credentials in keyring"""
    keyring.set_password(SERVICE_NAME, f'{profile_name}_access', access_key)
    keyring.set_password(SERVICE_NAME, f'{profile_name}_secret', secret_key)

def load_config():
    """Load configuration file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {
            'ui': {'theme': 'default', 'default_download_folder': '', 'default_upload_folder': ''},
            'profiles': [],
            'last_profile': None,
            'ssl': {'verify': True, 'ca_file': ''}
        }

def save_config(config):
    """Save configuration file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def setup_wasabi_profile():
    """Set up a Wasabi profile with user input"""
    print("=== Wasabi S3 File Manager Setup ===")
    print("This script will help you configure your Wasabi credentials.")
    print()
    
    # Get user inputs
    profile_name = input("Enter a profile name (e.g., 'wasabi-main'): ").strip()
    if not profile_name:
        print("Profile name is required!")
        return False
    
    bucket_name = input("Enter your bucket name (e.g., 'navoahansen'): ").strip()
    if not bucket_name:
        print("Bucket name is required!")
        return False
    
    access_key = input("Enter your Wasabi access key: ").strip()
    if not access_key:
        print("Access key is required!")
        return False
    
    secret_key = getpass.getpass("Enter your Wasabi secret key: ").strip()
    if not secret_key:
        print("Secret key is required!")
        return False
    
    endpoint_url = input("Enter endpoint URL (press Enter for default 'https://s3.wasabisys.com'): ").strip()
    if not endpoint_url:
        endpoint_url = 'https://s3.wasabisys.com'
    
    print()
    print("Configuration Summary:")
    print(f"Profile Name: {profile_name}")
    print(f"Bucket Name: {bucket_name}")
    print(f"Access Key: {access_key[:4]}***{access_key[-4:] if len(access_key) > 8 else '***'}")
    print(f"Secret Key: ***hidden***")
    print(f"Endpoint URL: {endpoint_url}")
    print()
    
    confirm = input("Save this configuration? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Configuration cancelled.")
        return False
    
    try:
        # Store credentials securely
        store_credential(profile_name, access_key, secret_key)
        print("✓ Credentials stored securely")
        
        # Update configuration
        config = load_config()
        
        # Remove any existing profiles with the same name
        config['profiles'] = [p for p in config['profiles'] if p.get('name') != profile_name]
        
        # Add new profile
        profile = {
            'name': profile_name,
            'bucket_name': bucket_name,
            'endpoint_url': endpoint_url,
            'ssl_verify': True,
            'ca_file': ''
        }
        
        config['profiles'].append(profile)
        config['last_profile'] = profile_name
        
        save_config(config)
        print("✓ Configuration saved")
        
        print()
        print("Setup completed successfully!")
        print("You can now start the Wasabi File Manager and select your profile.")
        return True
        
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False

def test_credentials():
    """Test the stored credentials"""
    print("\n=== Testing Connection ===")
    
    config = load_config()
    if not config['profiles']:
        print("No profiles configured. Run setup first.")
        return False
    
    # Use the last profile or first available
    profile = config['profiles'][-1]
    profile_name = profile['name']
    bucket_name = profile['bucket_name']
    endpoint_url = profile['endpoint_url']
    
    try:
        # Get credentials
        access_key = keyring.get_password(SERVICE_NAME, f'{profile_name}_access')
        secret_key = keyring.get_password(SERVICE_NAME, f'{profile_name}_secret')
        
        if not access_key or not secret_key:
            print("Credentials not found in keyring. Run setup first.")
            return False
        
        # Test connection
        import boto3
        s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url
        )
        
        # Try to list objects in the bucket
        print(f"Testing connection to bucket '{bucket_name}'...")
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        
        print("✓ Connection successful!")
        print(f"✓ Can access bucket '{bucket_name}'")
        
        if 'Contents' in response:
            print(f"✓ Found {len(response['Contents'])} objects")
        else:
            print("✓ Bucket is empty or no objects found")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nPossible issues:")
        print("- Check your access key and secret key")
        print("- Verify the bucket name is correct")
        print("- Ensure the bucket exists and you have permissions")
        print("- Check your internet connection")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_credentials()
    else:
        setup_wasabi_profile()

if __name__ == "__main__":
    main()
