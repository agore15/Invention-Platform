import os
import hashlib
import spacy
from google.cloud import storage, firestore
from crawler import config

# Configuration
BUCKET_NAME = 'invention-platform-data-001'
PROJECT_ID = 'still-manifest-478014-c1'

def backfill():
    print("Initializing Backfill...")
    db = firestore.Client(project=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # Load Spacy (Match Dataflow version)
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        from spacy.cli import download
        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
        
    blobs = list(bucket.list_blobs(prefix='specs/processed/'))
    print(f"Found {len(blobs)} specs to process.")
    
    batch = db.batch()
    batch_count = 0
    total_docs = 0
    
    for blob in blobs:
        if not blob.name.endswith('.txt'):
            continue
            
        print(f"Processing {blob.name}...")
        content = blob.download_as_text()
        
        path = f"gs://{BUCKET_NAME}/{blob.name}"
        filename = blob.name.split('/')[-1]
        spec_name = filename.replace('.txt', '')
        
        metadata = {
            'source': f'3GPP TS {spec_name}',
            'gcs_uri': path,
            'type': 'Technical Specification'
        }
        
        # EXACT REPLICATION OF DATAFLOW LOGIC
        # -----------------------------------
        doc = nlp(content[:1000000]) 
        current_chunk = []
        current_length = 0
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if not sent_text:
                continue
                
            current_chunk.append(sent_text)
            current_length += len(sent_text)
            
            if current_length >= 500:
                chunk_text = " ".join(current_chunk)
                doc_id = hashlib.md5(chunk_text.encode('utf-8')).hexdigest()
                
                # Add to Batch
                doc_ref = db.collection('3gpp_knowledge_base').document(doc_id)
                batch.set(doc_ref, {
                    'text': chunk_text,
                    'metadata': metadata
                })
                batch_count += 1
                total_docs += 1
                
                if batch_count >= 400:
                    batch.commit()
                    print(f"  Committed batch of 400 chunks. Total: {total_docs}")
                    batch = db.batch()
                    batch_count = 0
                
                current_chunk = []
                current_length = 0
        
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            doc_id = hashlib.md5(chunk_text.encode('utf-8')).hexdigest()
            doc_ref = db.collection('3gpp_knowledge_base').document(doc_id)
            batch.set(doc_ref, {
                'text': chunk_text,
                'metadata': metadata
            })
            batch_count += 1
            total_docs += 1
            
    if batch_count > 0:
        batch.commit()
        print(f"Final batch committed. Total Docs: {total_docs}")

if __name__ == "__main__":
    backfill()
