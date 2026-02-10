#!/usr/bin/env python3
"""Test script to check GCS emulator and list uploaded files"""

import os

from dotenv import load_dotenv

from app.services.storage import StorageService

load_dotenv()


def main():
    try:
        storage = StorageService()
        print("Connected to storage service")
        print(f"Bucket: {storage.bucket_name}")
        print(
            f"Emulator: {os.getenv('STORAGE_EMULATOR_HOST', 'Not set (using production)')}\n"
        )

        # List all blobs in bucket
        blobs = list(storage.bucket.list_blobs())

        if blobs:
            print(f"Found {len(blobs)} file(s) in bucket:\n")
            for blob in blobs:
                print(f"  - {blob.name}")
                print(f"    Size: {blob.size} bytes")
                print(f"    URL: {blob.public_url}\n")
        else:
            print("No files found in bucket")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("  1. STORAGE_EMULATOR_HOST is set (e.g., http://localhost:4443)")
        print("  2. GCS_BUCKET_NAME is set (e.g., spotdate-oauth-flow)")
        print("  3. GCS emulator is running and the bucket exists")


if __name__ == "__main__":
    main()
