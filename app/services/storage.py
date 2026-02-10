"""Google Cloud Storage service for data persistence"""

import json
import os
from typing import Optional

from dotenv import load_dotenv
from google.api_core import client_options as client_options_lib
from google.auth import default
from google.cloud import storage

load_dotenv()

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")


class StorageService:
    """Service for uploading data to Google Cloud Storage"""

    def __init__(self):
        """Initialize GCS client with default credentials"""
        credentials, _ = default()

        # Check for emulator configuration for local development
        emulator_host = os.getenv("STORAGE_EMULATOR_HOST")
        if emulator_host:
            client_options = client_options_lib.ClientOptions(
                api_endpoint=emulator_host
            )
            self.client = storage.Client(
                credentials=credentials, client_options=client_options
            )
        else:
            self.client = storage.Client(credentials=credentials)

        self.bucket_name = GCS_BUCKET_NAME

        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is not set")

        self.bucket = self.client.bucket(self.bucket_name)

    def upload_json(self, data: dict, blob_name: str) -> Optional[str]:
        """
        Upload a dictionary as a JSON file to GCS bucket

        Args:
            data: Dictionary to upload
            blob_name: Name of the blob in GCS (e.g., 'user_id/artists_2024-02-09.json')

        Returns:
            Public URL of the uploaded blob, or None if upload fails

        Raises:
            ValueError: If bucket name is not configured
            Exception: If upload fails
        """
        try:
            blob = self.bucket.blob(blob_name)

            # Convert dict to JSON and upload
            json_data = json.dumps(data, indent=2)
            blob.upload_from_string(
                json_data,
                content_type="application/json",
            )

            return blob.public_url
        except Exception as e:
            raise Exception(f"Failed to upload {blob_name} to GCS: {str(e)}")
