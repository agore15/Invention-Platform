import numpy as np
import re
from typing import List, Dict, Any
from google.cloud import aiplatform_v1
from brain.vectorizer import EmbeddingGenerator
from brain.docstore import DocStore
from crawler import config

class CloudSearcher:
    def __init__(self):
        print('Initializing Cloud Searcher (Gapic)...')
        self.embedder = EmbeddingGenerator()
        self.docstore = DocStore()
        self.client = None
        
        # Hardcoded Public Domain (Dynamic lookup is flimsy)
        # Use gcloud output: 710037152.us-central1-941721845440.vdb.vertexai.goog
        self.api_endpoint = "710037152.us-central1-941721845440.vdb.vertexai.goog"
        self.index_endpoint_path = f"projects/{config.PROJECT_ID}/locations/{config.REGION}/indexEndpoints/{config.VECTOR_INDEX_ENDPOINT_ID.split('/')[-1]}"
        self.deployed_index_id = "deployed_3gpp_index_v2"

        try:
            print(f"Connecting to Public Domain: {self.api_endpoint}")
            client_options = {"api_endpoint": self.api_endpoint}
            self.client = aiplatform_v1.MatchServiceClient(client_options=client_options)
            print("Gapic Client Initialized.")
        except Exception as e:
            print(f"Warning: Client init failed: {e}")

    def get_unique_metadata_values(self, key: str) -> List[str]:
        if key == 'type':
            return ['Technical Specification', 'TS', 'TR', 'CR', 'LS', 'WID']
        elif key == 'status':
            return ['Agreed', 'Draft', 'Withdrawn', 'Approved']
        elif key == 'source':
            return ['3GPP', 'Samsung', 'Huawei', 'Ericsson', 'Qualcomm', 'Nokia']
        return []

    def search(self, query: str, top_k: int = 5, filters: Dict[str, Any] = None, must_have_terms: List[str] = None) -> List[Dict[str, Any]]:
        if not self.client:
            print('Client unavailable.')
            return []

        # 1. Embed Query
        query_vectors = self.embedder.generate_embeddings([{'text': query, 'metadata': {}}])
        if not query_vectors:
            return []
        
        query_emb = query_vectors[0].embedding
        
        # 2. Search Vertex AI (Gapic)
        fetch_k = 50 if must_have_terms else top_k
        
        try:
            request = aiplatform_v1.FindNeighborsRequest(
                index_endpoint=self.index_endpoint_path,
                deployed_index_id=self.deployed_index_id,
                queries=[
                    aiplatform_v1.FindNeighborsRequest.Query(
                        datapoint=aiplatform_v1.IndexDatapoint(
                            feature_vector=query_emb
                        ),
                        neighbor_count=fetch_k
                    )
                ],
                return_full_datapoint=False
            )
            
            response = self.client.find_neighbors(request=request)
            
            # 3. Process Results
            results = []
            if response.nearest_neighbors:
                # Iterate neighbors of the first query
                for neighbor in response.nearest_neighbors[0].neighbors:
                    doc_id = neighbor.datapoint.datapoint_id
                    dist = neighbor.distance
                    
                    # Fetch content
                    doc = self.docstore.get_document(doc_id)
                    
                    if doc:
                        text_content = doc.get('text', '')
                        
                        # 4. Apply Keyword Constraints (Post-Filter)
                        if must_have_terms:
                            text_lower = text_content.lower()
                            if not any(term.lower() in text_lower for term in must_have_terms):
                                continue 
                                
                        results.append({
                            'id': doc_id,
                            'score': dist, 
                            'text': text_content,
                            'metadata': doc.get('metadata', {}),
                            'bm25_score': 0.0,
                            'vector_score': dist
                        })
                        
                        if len(results) >= top_k:
                            break
                    else:
                        pass
                        
            return results
            
        except Exception as e:
            print(f'Vertex Search failed (Gapic): {e}')
            return []
