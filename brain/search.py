from typing import List, Dict, Any, Optional
import numpy as np
from rank_bm25 import BM25Okapi

class HybridSearcher:
    def __init__(self):
        self.bm25 = None
        self.chunks = [] # Local cache of chunks for BM25
        self.corpus = [] # Tokenized corpus for BM25

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """Indexes chunks for BM25."""
        self.chunks = chunks
        # Simple tokenization: split by space and lowercase
        self.corpus = [chunk['text'].lower().split(" ") for chunk in chunks] 
        self.bm25 = BM25Okapi(self.corpus)

    def search(self, query: str, top_k: int = 5, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """
        Performs hybrid search.
        alpha: Weight for vector search (0.0 to 1.0). 1.0 = pure vector, 0.0 = pure keyword.
        """
        # 1. Keyword Search (BM25)
        if not self.bm25:
            print("Warning: BM25 not indexed.")
            bm25_scores = np.zeros(len(self.chunks))
        else:
            tokenized_query = query.lower().split(" ")
            bm25_scores = self.bm25.get_scores(tokenized_query)
            # Normalize BM25 scores
            if bm25_scores.max() > 0:
                bm25_scores = bm25_scores / bm25_scores.max()

        # 2. Vector Search
        # Placeholder for vector scores
        vector_scores = np.zeros(len(self.chunks))
        
        # Combine scores
        # Note: This assumes 1-to-1 mapping between chunks in BM25 and Vector DB
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
