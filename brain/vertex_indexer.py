import time
import json
from typing import List, Optional, Dict, Any
from google.cloud import aiplatform
from google.cloud import storage
from google.cloud.aiplatform.matching_engine import matching_engine_index_endpoint
from brain.vectorizer import VectorizedChunk
from crawler import config
import hashlib

class VertexAIIndexer:
    def __init__(self, 
                 project_id: str = config.PROJECT_ID, 
                 location: str = config.REGION,
                 index_display_name: str = config.VECTOR_INDEX_DISPLAY_NAME,
                 endpoint_display_name: str = config.VECTOR_INDEX_ENDPOINT_DISPLAY_NAME):
        
        self.project_id = project_id
        self.location = location
        self.index_display_name = index_display_name
        self.endpoint_display_name = endpoint_display_name
        
        aiplatform.init(project=project_id, location=location)

    def create_index(self):
        print(f'Creating/Retrieving Index: {self.index_display_name}...')
        indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name={self.index_display_name}')
        if indexes:
            self.index = indexes[0]
            print(f'Found existing index: {self.index.resource_name}')
        else:
            print('Creating new Index (Brute Force)...')
            self.index = aiplatform.MatchingEngineIndex.create_brute_force_index(
                display_name=self.index_display_name,
                contents_delta_uri=f'gs://{config.GCS_BUCKET_NAME}/vector_search_staging/',
                dimensions=768,
                distance_measure_type='DOT_PRODUCT_DISTANCE',
                description='3GPP Knowledge Base Index'
            )
            print(f'Index created: {self.index.resource_name}')

    def create_endpoint_and_deploy(self):
        print(f'Creating/Retrieving Endpoint: {self.endpoint_display_name}...')
        # Note: We rely on ID now in Config for search, but here we might still list by name for management
        # If name is '...-endpoint', it finds the public one we confirmed exists.
        endpoints = aiplatform.MatchingEngineIndexEndpoint.list(filter=f'display_name={self.endpoint_display_name}')
        if endpoints:
            self.endpoint = endpoints[0]
            print(f'Found existing endpoint: {self.endpoint.resource_name}')
        else:
            print("Creating NEW endpoint with public_endpoint_enabled=True...")
            self.endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
                display_name=self.endpoint_display_name,
                public_endpoint_enabled=True
            )
            print(f'Endpoint created: {self.endpoint.resource_name}')
        
        # FIX: Ensure index is initialized
        if not hasattr(self, 'index'):
             self.create_index()

        if not self.endpoint.deployed_indexes:
            print('Deploying index to endpoint (this takes ~15-20 mins)...')
            self.endpoint.deploy_index(
                index=self.index,
                deployed_index_id='deployed_3gpp_index_v1'
            )
            print('Index deployed.')
        else:
            print('Index already deployed.')

    def upload_vectors(self, vectorized_chunks: List[VectorizedChunk]):
        print(f'Preparing {len(vectorized_chunks)} vectors for Vertex AI update...')
        
        # 1. Convert to JSONL format required by Vertex AI
        jsonl_lines = []
        for chunk in vectorized_chunks:
            # Generate ID
            doc_id = hashlib.md5(chunk.text.encode('utf-8')).hexdigest()
            
            # Use 'allow_list' for schema correctness
            record = {
                'id': doc_id,
                'embedding': chunk.embedding,
                'restricts': [
                    {'namespace': 'source', 'allow_list': [chunk.metadata.get('source', 'unknown')]},
                    {'namespace': 'type', 'allow_list': [chunk.metadata.get('type', 'TS')]}
                ]
            }
            jsonl_lines.append(json.dumps(record))
            
        # 2. Upload JSONL to GCS
        storage_client = storage.Client(project=self.project_id)
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        
        timestamp = int(time.time())
        blob_name = f'vector_search_staging/update_{timestamp}.json'
        blob = bucket.blob(blob_name)
        
        content = '\n'.join(jsonl_lines)
        blob.upload_from_string(content)
        print(f'Uploaded batch to gs://{config.GCS_BUCKET_NAME}/{blob_name}')
        
        # 3. Trigger Upsert (Streaming)
        if not hasattr(self, 'index'):
             self.create_index()
             
        print('Triggering Index Update (Streaming)...')
        
        try:
            datapoints = []
            for chunk in vectorized_chunks:
                 doc_id = hashlib.md5(chunk.text.encode('utf-8')).hexdigest()
                 datapoints.append({
                     'datapoint_id': doc_id,
                     'feature_vector': chunk.embedding,
                     'restricts': [
                        {'namespace': 'source', 'allow_list': [chunk.metadata.get('source', 'unknown')]},
                        {'namespace': 'type', 'allow_list': [chunk.metadata.get('type', 'TS')]}
                     ]
                 })
            
            self.index.upsert_datapoints(datapoints=datapoints)
            print('Successfully upserted datapoints via Streaming API.')
            
        except Exception as e:
            print(f'Streaming upsert failed ({e}). Proceeding to verify GCS file presence only.')
