import os
import glob
from google.cloud import storage
from crawler import config

def migrate_local():
    print(f'Starting migration of local data to {config.GCS_BUCKET_NAME}...')
    
    storage_client = storage.Client(project=config.PROJECT_ID)
    bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
    
    local_dir = 'data/specs'
    files = glob.glob(os.path.join(local_dir, '*.txt'))
    
    if not files:
        print('No local files found to migrate.')
        return

    print(f'Found {len(files)} local files to upload.')
    
    for file_path in files:
        filename = os.path.basename(file_path)
        blob_name = f'specs/processed/{filename}'
        
        blob = bucket.blob(blob_name)
        print(f'Uploading {filename} to gs://{config.GCS_BUCKET_NAME}/{blob_name}...')
        
        try:
            blob.upload_from_filename(file_path)
            print('  Success.')
        except Exception as e:
            print(f'  Failed: {e}')

    print('Migration complete.')

if __name__ == '__main__':
    migrate_local()
