import os
import sys
import hashlib
from crawler import config
from brain.indexer import ChunkingStrategy
from brain.vectorizer import EmbeddingGenerator
from brain.vertex_indexer import VertexAIIndexer
from brain.docstore import DocStore
from google.cloud import storage

# Ensure project root in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_cloud_pipeline():
    print('=== Starting 3GPP Cloud Pipeline (Firestore Enabled) ===')

    # 1. Load from GCS
    print('\n[Phase 1] LoadingSpecs from GCS...')
    storage_client = storage.Client(project=config.PROJECT_ID)
    bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix='specs/processed/'))
    
    print(f'Found {len(blobs)} specification files in gs://{config.GCS_BUCKET_NAME}/specs/processed/')
    
    chunker = ChunkingStrategy()
    all_chunks = []

    for blob in blobs:
        if not blob.name.endswith('.txt'):
            continue
            
        print(f'  Processing {blob.name}...')
        try:
            text = blob.download_as_text()
            filename = os.path.basename(blob.name)
            spec_name = filename.replace('.txt', '')
            
            doc_data = {
                'content': text,
                'metadata': {
                    'source': f'3GPP TS {spec_name}',
                    'gcs_uri': f'gs://{config.GCS_BUCKET_NAME}/{blob.name}',
                    'type': 'Technical Specification'
                }
            }
            
            if '\\n' in text:
                 doc_data['content'] = text.replace('\\n', '\n')

            chunks = chunker.chunk_document(doc_data)
            all_chunks.extend(chunks)
            print(f'    -> Extracted {len(chunks)} chunks.')
            
        except Exception as e:
            print(f'    Error processing {blob.name}: {e}')

    # 2. Embed & Index & Store Text
    print(f'\n[Phase 2] Embedding, Indexing, and Storing {len(all_chunks)} chunks...')
    if all_chunks:
        # Initialize Services
        docstore = DocStore()
        embedder = EmbeddingGenerator()
        
        # A. Embed in batches
        vectorized_chunks = embedder.generate_embeddings(all_chunks)
        
        # B. Store Text in Firestore
        print('  Uploading Text to Firestore...')
        for chunk in vectorized_chunks:
            # Re-generate ID to ensure consistency
            doc_id = hashlib.md5(chunk.text.encode('utf-8')).hexdigest()
            docstore.upsert_document(doc_id, chunk.text, chunk.metadata)
            
        # C. Store Vectors in Vertex AI
        print('  Uploading Vectors to Vertex AI...')
        indexer = VertexAIIndexer()
        indexer.create_endpoint_and_deploy() 
        
        if indexer.endpoint and indexer.endpoint.deployed_indexes:
            indexer.upload_vectors(vectorized_chunks)
            print('  Cloud Indexing Complete!')
        else:
            print('  Endpoint not ready. Text stored in Firestore, but Vectors pending upload.')
    else:
        print('No chunks to index.')

if __name__ == '__main__':
    run_cloud_pipeline()
