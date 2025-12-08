import os
import sys
import json
from typing import List, Dict, Any

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.vectorizer import EmbeddingGenerator, Indexer, VectorizedChunk

def chunk_text_func(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def ingest():
    specs_dir = 'data/specs'
    files = [f for f in os.listdir(specs_dir) if f.endswith('.txt') and os.path.getsize(os.path.join(specs_dir, f)) > 1000]
    
    all_chunks = []
    
    for f in files:
        print(f'Processing {f}...')
        spec_name = f.replace('.txt', '')
        with open(os.path.join(specs_dir, f), 'r', encoding='utf-8') as file:
            text = file.read()
            
        text_chunks = chunk_text_func(text)
        for i, chunk_content in enumerate(text_chunks):
            all_chunks.append({
                'text': chunk_content,
                'metadata': {
                    'source': f'3GPP TS {spec_name}',
                    'title': f'{spec_name} Technical Specification',
                    'chunk_id': i
                }
            })
            
    print(f'Generated {len(all_chunks)} chunks.')
    
    # Embed
    gen = EmbeddingGenerator()
    vectors = gen.generate_embeddings(all_chunks)
    
    # Index
    indexer = Indexer()
    indexer.upload_vectors(vectors)
    print('Ingestion complete.')

if __name__ == '__main__':
    ingest()
