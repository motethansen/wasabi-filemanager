#!/usr/bin/env python3
"""
Enhanced test script for Wasabi S3 connection with debugging
"""

import boto3
import json
import keyring
from botocore.exceptions import ClientError, NoCredentialsError
import sys

# Constants
CONFIG_FILE = 'app_config.json'
SERVICE_NAME = 'WasabiFileManager'

def load_config():
    """Load configuration file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_wasabi_connection():
    """Test Wasabi connection with various configurations"""
    print("=== Wasabi Connection Test ===")
    
    # Load config
    config = load_config()
    if not config or not config.get('profiles'):
        print("No profiles found in configuration")
        return False
    
    profile = config['profiles'][0]
    profile_name = profile['name']
    bucket_name = profile['bucket_name']
    
    # Get credentials
    try:
        access_key = keyring.get_password(SERVICE_NAME, f'{profile_name}_access')
        secret_key = keyring.get_password(SERVICE_NAME, f'{profile_name}_secret')
        
        if not access_key or not secret_key:
            print("No credentials found in keyring")
            return False
        
        print(f"Profile: {profile_name}")
        print(f"Bucket: {bucket_name}")
        print(f"Access Key: {access_key[:4]}***{access_key[-4:]}")
        print(f"Secret Key: ***hidden***")
        print()
        
    except Exception as e:
        print(f"Error retrieving credentials: {e}")
        return False
    
    # Test different endpoint configurations
    endpoints_to_test = [
        'https://s3.ap-southeast-1.wasabisys.com',  # Try the correct region first
        'https://s3.wasabisys.com',
        'https://s3.us-east-1.wasabisys.com',
        'https://s3.us-west-1.wasabisys.com',
        'https://s3.eu-central-1.wasabisys.com'
    ]
    
    for endpoint in endpoints_to_test:
        print(f"Testing endpoint: {endpoint}")
        
        try:
            # Create S3 client
            s3 = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                endpoint_url=endpoint,
                region_name='us-east-1'  # Try with explicit region
            )
            
            # Test bucket access
            response = s3.head_bucket(Bucket=bucket_name)
            print(f"✓ Bucket access successful with {endpoint}")
            
            # Test listing objects
            response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
            print(f"✓ Object listing successful")
            
            if 'Contents' in response:
                print(f"✓ Found {len(response['Contents'])} objects")
                for obj in response['Contents'][:3]:  # Show first 3 objects
                    print(f"  - {obj['Key']} ({obj['Size']} bytes)")
            else:
                print("✓ Bucket is empty")
            
            # Test with region detection
            try:
                response = s3.get_bucket_location(Bucket=bucket_name)
                region = response.get('LocationConstraint', 'us-east-1')
                print(f"✓ Bucket region: {region}")
            except Exception as e:
                print(f"! Could not detect region: {e}")
            
            print(f"✓ SUCCESS: Connection works with {endpoint}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"✗ ClientError with {endpoint}: {error_code} - {error_message}")
            
            if error_code == 'SignatureDoesNotMatch':
                print("  This usually means incorrect credentials or clock skew")
            elif error_code == 'AccessDenied':
                print("  This means credentials are valid but insufficient permissions")
            elif error_code == 'NoSuchBucket':
                print("  This means the bucket doesn't exist or is in a different region")
            
        except NoCredentialsError:
            print(f"✗ No credentials error with {endpoint}")
            
        except Exception as e:
            print(f"✗ Other error with {endpoint}: {e}")
        
        print()
    
    print("All endpoints failed. Please check:")
    print("1. Your access key and secret key are correct")
    print("2. The bucket name 'navoahansen' is correct")
    print("3. The bucket exists and you have permissions")
    print("4. Your system clock is synchronized")
    return False

def interactive_test():
    """Interactive test with user input"""
    print("=== Interactive Wasabi Test ===")
    
    access_key = input("Enter your access key: ").strip()
    secret_key = input("Enter your secret key: ").strip()
    bucket_name = input("Enter your bucket name: ").strip()
    
    if not all([access_key, secret_key, bucket_name]):
        print("All fields are required")
        return False
    
    endpoint = input("Enter endpoint URL (or press Enter for default): ").strip()
    if not endpoint:
        endpoint = 'https://s3.wasabisys.com'
    
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint
        )
        
        print(f"Testing connection to {bucket_name} at {endpoint}...")
        
        # Test bucket access
        response = s3.head_bucket(Bucket=bucket_name)
        print("✓ Bucket access successful")
        
        # Test listing
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
        print("✓ Object listing successful")
        
        if 'Contents' in response:
            print(f"Found {len(response['Contents'])} objects:")
            for obj in response['Contents']:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("Bucket is empty")
        
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        interactive_test()
    else:
        test_wasabi_connection()

if __name__ == "__main__":
    main()
