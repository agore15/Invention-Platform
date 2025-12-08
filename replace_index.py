from google.cloud import aiplatform
from crawler import config
import time

def replace_index():
    aiplatform.init(project=config.PROJECT_ID, location=config.REGION)
    
    # 1. Create NEW Index (v2) with data
    print("Creating NEW Index (v2) from GCS data...")
    try:
        new_index = aiplatform.MatchingEngineIndex.create_brute_force_index(
            display_name=f"{config.VECTOR_INDEX_DISPLAY_NAME}-v2",
            contents_delta_uri=f"gs://{config.GCS_BUCKET_NAME}/vector_search_staging/",
            dimensions=768,
            distance_measure_type="DOT_PRODUCT_DISTANCE",
            description="3GPP Knowledge Base Index V2 (Populated)",
            sync=True # Wait for creation
        )
        print(f"New Index Created: {new_index.resource_name}")
    except Exception as e:
        print(f"Index creation failed: {e}")
        return

    # 2. Get Endpoint
    endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=config.VECTOR_INDEX_ENDPOINT_ID
    )
    print(f"Found Endpoint: {endpoint.resource_name}")

    # 3. Deploy New Index
    print("Deploying New Index (v2)...")
    try:
        endpoint.deploy_index(
            index=new_index,
            deployed_index_id="deployed_3gpp_index_v2",
            display_name="v2_deployment"
        )
        print("New Index Deployed successfully.")
    except Exception as e:
        print(f"Deployment failed: {e}")
        return

    # 4. Undeploy Old Index (Cleanup)
    print("Undeploying Old Index (v1)...")
    try:
        endpoint.undeploy_index(
            deployed_index_id="deployed_3gpp_index_v1"
        )
        print("Old Index Undeployed.")
    except Exception as e:
        print(f"Undeploy warning: {e}")

if __name__ == "__main__":
    replace_index()
