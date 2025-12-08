import time
from google.cloud import aiplatform
from crawler import config

# Override config for new endpoint
NEW_ENDPOINT_NAME = config.VECTOR_INDEX_ENDPOINT_DISPLAY_NAME + "-public"

def reprovision():
    print(f"Initializing Vertex AI (Project: {config.PROJECT_ID})...")
    aiplatform.init(project=config.PROJECT_ID, location=config.REGION)
    
    # 1. Get the Index
    print(f"Retrieving Index: {config.VECTOR_INDEX_DISPLAY_NAME}")
    indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name={config.VECTOR_INDEX_DISPLAY_NAME}')
    if not indexes:
        print("ERROR: Index not found! Cannot deploy.")
        return
    index = indexes[0]
    print(f"Found Index: {index.resource_name}")

    # 2. Check/Create New Public Endpoint
    print(f"Checking/Creating Endpoint: {NEW_ENDPOINT_NAME}")
    endpoints = aiplatform.MatchingEngineIndexEndpoint.list(filter=f'display_name={NEW_ENDPOINT_NAME}')
    
    if endpoints:
        endpoint = endpoints[0]
        print(f"Found existing endpoint: {endpoint.resource_name}")
    else:
        print("Creating NEW endpoint with public_endpoint_enabled=True...")
        endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
            display_name=NEW_ENDPOINT_NAME,
            public_endpoint_enabled=True
        )
        print(f"Created Endpoint: {endpoint.resource_name}")

    # 3. Deploy Index
    if not endpoint.deployed_indexes:
        print("Deploying Index (this WILL take ~20 mins)...")
        # deployed_index_id must be unique in the endpoint
        endpoint.deploy_index(
            index=index,
            deployed_index_id='deployed_3gpp_index_public_v1',
            machine_type='e2-standard-2',
            min_replica_count=1,
            max_replica_count=1
        )
        print("Index Deployed Successfully!")
    else:
        print("Index already deployed to this endpoint.")
        
    print(f"DONE. New Endpoint Public Domain: {endpoint.public_endpoint_domain_name}")

if __name__ == "__main__":
    reprovision()
