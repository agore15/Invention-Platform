from google.cloud import aiplatform
from crawler import config
import time

def trigger_update():
    # Initialize
    aiplatform.init(project=config.PROJECT_ID, location=config.REGION)
    
    # Get Index
    print(f"Retrieving Index: {config.VECTOR_INDEX_DISPLAY_NAME}")
    indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name={config.VECTOR_INDEX_DISPLAY_NAME}')
    if not indexes:
        print("Index not found!")
        return
        
    index = indexes[0]
    print(f"Index found: {index.resource_name}")
    
    # Trigger Update
    # We update the index to "poke" it to check the contents_delta_uri
    # Or strictly speaking, we might just need to wait. 
    # But calling update() with the SAME delta_uri often triggers a sync check.
    print("Triggering Batch Update (Syncing GCS to Index)...")
    
    try:
        # We re-set the description to current time to force an update op
        timestamp = int(time.time())
        index.update(
            description=f'3GPP Knowledge Base Index (Updated {timestamp})',
            display_name=config.VECTOR_INDEX_DISPLAY_NAME
        )
        print("Update operation initiated successfully.")
    except Exception as e:
        print(f"Update failed: {e}")

if __name__ == "__main__":
    trigger_update()
