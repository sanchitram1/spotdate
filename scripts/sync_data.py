import os

from google.cloud import storage

# Configuration
BUCKET_NAME = "spotdate-oauth-flow"
LOCAL_DIR = "fetched_data"


def download_blob(bucket, blob):
    """Downloads a blob to the local directory, preserving folder structure."""
    # Create local path (e.g., downloaded_data/user_123/artists.json)
    local_path = os.path.join(LOCAL_DIR, blob.name)
    local_folder = os.path.dirname(local_path)

    # Ensure local folder exists
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    # Download
    print(f"Downloading {blob.name} ...")
    blob.download_to_filename(local_path)


def sync_bucket():
    # Initialize client (looks for local gcloud creds automatically)
    storage_client = storage.Client()

    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blobs = list(bucket.list_blobs())

        if not blobs:
            print(f"Bucket {BUCKET_NAME} is empty!")
            return

        print(f"Found {len(blobs)} files. Syncing to '{LOCAL_DIR}/'...")

        for blob in blobs:
            # Skip folders/trailing slashes if any
            if blob.name.endswith("/"):
                continue
            download_blob(bucket, blob)

        print("\n✅ Sync complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Did you run 'gcloud auth application-default login'?")


if __name__ == "__main__":
    sync_bucket()
