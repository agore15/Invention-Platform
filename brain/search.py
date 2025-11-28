from typing import List, Dict, Any, Optional
import numpy as np
from rank_bm25 import BM25Okapi
import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.vectorizer import EmbeddingGenerator

class HybridSearcher:
    def __init__(self, index_file: str = "brain/index.json"):
        self.index_file = index_file
        self.bm25 = None
        self.chunks = []
        self.corpus = []
        self.vectors = [] # Numpy array of embeddings
        self.embedder = EmbeddingGenerator() # For query embedding

        self._load_index()

    def _load_index(self):
        if not os.path.exists(self.index_file):
            print(f"Warning: Index file {self.index_file} not found.")
            return

        print(f"Loading index from {self.index_file}...")
        with open(self.index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.chunks = data
        self.corpus = [chunk['text'].lower().split(" ") for chunk in data]
        self.bm25 = BM25Okapi(self.corpus)
        
        # Load vectors into numpy array
        embeddings = [chunk['embedding'] for chunk in data]
        if embeddings:
            self.vectors = np.array(embeddings)
        else:
            self.vectors = np.array([])
            
        print(f"Loaded {len(self.chunks)} chunks.")

    def search(self, query: str, top_k: int = 5, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """
        Performs hybrid search.
        alpha: Weight for vector search (0.0 to 1.0). 1.0 = pure vector, 0.0 = pure keyword.
        """
        if not self.chunks:
            print("Index is empty.")
            return []

        # 1. Keyword Search (BM25)
        tokenized_query = query.lower().split(" ")
        bm25_scores = self.bm25.get_scores(tokenized_query)
        # Normalize BM25 scores (0-1)
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max()

        # 2. Vector Search
        # Embed query
        query_vectors = self.embedder.generate_embeddings([{"text": query, "metadata": {}}])
        if not query_vectors:
            print("Failed to embed query.")
            vector_scores = np.zeros(len(self.chunks))
        else:
            query_vec = np.array(query_vectors[0].embedding)
            
            # Cosine Similarity: (A . B) / (|A| * |B|)
            # Assuming vectors are normalized? If not, we should normalize.
            # For simplicity, let's just do dot product if normalized, or full cosine.
            
            # Normalize query
            norm_q = np.linalg.norm(query_vec)
            if norm_q > 0:
                query_vec = query_vec / norm_q
                
            # Normalize doc vectors
            # (Ideally pre-compute this)
            norm_docs = np.linalg.norm(self.vectors, axis=1)
            # Avoid divide by zero
            norm_docs[norm_docs == 0] = 1
            
            normalized_vectors = self.vectors / norm_docs[:, np.newaxis]
            
            vector_scores = np.dot(normalized_vectors, query_vec)
            # Clip to 0-1 (cosine similarity is -1 to 1, but for text usually 0-1)
            vector_scores = np.clip(vector_scores, 0, 1)

        # 3. Combine scores
        hybrid_scores = (1 - alpha) * bm25_scores + alpha * vector_scores
        
        # Get top K
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if hybrid_scores[idx] > 0:
                results.append({
                    "chunk": self.chunks[idx],
                    "score": float(hybrid_scores[idx]),
                    "bm25_score": float(bm25_scores[idx]),
                    "vector_score": float(vector_scores[idx])
                })
                
        return results

if __name__ == "__main__":
    # Test
    searcher = HybridSearcher()
    results = searcher.search("hello", top_k=2)
    for res in results:
        print(f"Score: {res['score']:.4f} | Text: {res['chunk']['text']}")
