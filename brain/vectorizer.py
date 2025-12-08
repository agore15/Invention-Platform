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
    def __init__(self, model_name: str = 'text-embedding-004'):
        self.model_name = model_name
        self.model = None

    def _load_model(self):
        if not self.model:
            try:
                self.model = TextEmbeddingModel.from_pretrained(self.model_name)
            except Exception as e:
                print(f'Error loading model {self.model_name}: {e}')
                pass

    def generate_embeddings(self, chunks: List[Dict[str, Any]], batch_size: int = 5) -> List[VectorizedChunk]:
        self._load_model()
        vectorized_chunks = []
        texts = [chunk['text'] for chunk in chunks]
        
        if not self.model:
            print('Warning: Model not loaded. Using mock embeddings.')
            for chunk in chunks:
                vectorized_chunks.append(VectorizedChunk(
                    text=chunk['text'],
                    embedding=[0.1] * 768,
                    metadata=chunk['metadata']
                ))
            return vectorized_chunks

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_chunks = chunks[i : i + batch_size]
            inputs = [TextEmbeddingInput(text, 'RETRIEVAL_DOCUMENT') for text in batch_texts]
            try:
                batch_embeddings = self.model.get_embeddings(inputs)
                for j, embedding in enumerate(batch_embeddings):
                    vectorized_chunks.append(VectorizedChunk(
                        text=batch_chunks[j]['text'],
                        embedding=embedding.values,
                        metadata=batch_chunks[j]['metadata']
                    ))
                time.sleep(0.1) 
            except Exception as e:
                print(f'Error generating embeddings for batch {i}: {e}')
                continue
        return vectorized_chunks

class Indexer:
    def __init__(self, index_file: str = 'brain/index.json'):
        self.index_file = index_file
        
    def upload_vectors(self, vectorized_chunks: List[VectorizedChunk]):
        print(f'Saving {len(vectorized_chunks)} vectors to {self.index_file}...')
        data = []
        for chunk in vectorized_chunks:
            data.append({
                'text': chunk.text,
                'embedding': chunk.embedding,
                'metadata': chunk.metadata
            })
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print('Index saved successfully.')
