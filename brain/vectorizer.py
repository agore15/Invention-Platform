import time
from typing import List, Optional, Dict, Any
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
from dataclasses import dataclass, asdict
import os
import json

@dataclass
class VectorizedChunk:
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]

class EmbeddingGenerator:
    def __init__(self, model_name: str = "text-embedding-004"):
        self.model_name = model_name
        self.model = None

    def _load_model(self):
        if not self.model:
            try:
                self.model = TextEmbeddingModel.from_pretrained(self.model_name)
            except Exception as e:
                print(f"Error loading model {self.model_name}: {e}")
                raise

    def generate_embeddings(self, chunks: List[Dict[str, Any]], batch_size: int = 5) -> List[VectorizedChunk]:
        """Generates embeddings for a list of chunk dicts (from parser)."""
        self._load_model()
        
        vectorized_chunks = []
        texts = [chunk['text'] for chunk in chunks]
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_chunks = chunks[i : i + batch_size]
            
            inputs = [TextEmbeddingInput(text, "RETRIEVAL_DOCUMENT") for text in batch_texts]
            try:
                batch_embeddings = self.model.get_embeddings(inputs)
                for j, embedding in enumerate(batch_embeddings):
                    vectorized_chunks.append(VectorizedChunk(
                        text=batch_chunks[j]['text'],
                        embedding=embedding.values,
                        metadata=batch_chunks[j]['metadata']
                    ))
                # Rate limiting precaution
                time.sleep(0.1) 
            except Exception as e:
                print(f"Error generating embeddings for batch {i}: {e}")
                # We might want to continue or raise. For now, let's print and continue
                continue
                
        return vectorized_chunks

class Indexer:
    def __init__(self, project_id: str, location: str, index_id: str = None):
        self.project_id = project_id
        self.location = location
        self.index_id = index_id
        # TODO: Initialize Vector Search Client
        
    def upload_vectors(self, vectorized_chunks: List[VectorizedChunk]):
        """Uploads vectors to the index."""
        # This is a placeholder for the actual upload logic
        # We need to format the data for Vector Search (e.g. JSONL for batch import or streaming)
        pass

