#!/usr/bin/env python
"""Create test bucket in GCS emulator"""

import os
from app.services.storage import StorageService
from dotenv import load_dotenv

load_dotenv()

def main():
    try:
        storage = StorageService()
        bucket_name = storage.bucket_name
        
        print(f"Checking bucket: {bucket_name}")
        
        if storage.bucket.exists():
            print(f"✓ Bucket '{bucket_name}' already exists")
        else:
            print(f"Creating bucket: {bucket_name}")
            storage.bucket.create()
            print(f"✓ Bucket created successfully")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
