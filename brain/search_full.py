from typing import List, Dict, Any, Optional  
import numpy as np  
import re  
from rank_bm25 import BM25Okapi  
import json  
import os  
import sys  
import datetime  
  
# Add project root to sys.path  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  
  
from brain.vectorizer import EmbeddingGenerator  
  
class HybridSearcher:  
    def __init__(self, index_file: str = " "brain/index.json):  
        self.index_file = index_file  
        self.bm25 = None  
        self.chunks = []  
        self.corpus = []  
        self.vectors = [] # Numpy array of embeddings  
        self.embedder = EmbeddingGenerator() # For query embedding  
  
        self._load_index() 
  
    def _log(self, msg: str):  
        with open("debug_search.log", "a", encoding="utf-8") as f:  
            f.write(f"{datetime.datetime.now()}: {msg}\n")  
  
    def _load_index(self):  
        if not os.path.exists(self.index_file):  
            print(f"Warning: Index file {self.index_file} not found.")  
            return  
  
        print(f"Loading index from {self.index_file}...")  
        with open(self.index_file, "r", encoding="utf-8") as f:  
            data = json.load(f)  
ECHO is on.
        self.chunks = data  
        self.corpus = [chunk["text"].lower().split(" ") for chunk in data]  
        self.bm25 = BM25Okapi(self.corpus)  
ECHO is on.
        # Load vectors into numpy array  
        embeddings = [chunk["embedding"] for chunk in data]  
        if embeddings:  
            self.vectors = np.array(embeddings)  
        else:  
            self.vectors = np.array([])  
ECHO is on.
        print(f"Loaded {len(self.chunks)} chunks.") 
  
    def _extract_phrases(self, query: str) - 
        """Extracts quoted phrases from the query and normalizes them."""  
  
    def search(self, query: str, top_k: int = 5, alpha: float = 0.5, filters: Dict[str, Any] = None, must_have_terms: List[str] = None) -, Any]]:  
        """ >> brain/search_full.py & echo         Performs hybrid search with optional metadata filtering and content constraints. >> brain/search_full.py & echo         alpha: Weight for vector search (0.0 to 1.0). 1.0 = pure vector, 0.0 = pure keyword. >> brain/search_full.py & echo         filters: Dictionary of metadata filters (e.g., {"type": "CR", "source": "Qualcomm"}). >> brain/search_full.py & echo         must_have_terms: List of strings. If provided, returned docs MUST contain at least one of these terms (case-insensitive). >> brain/search_full.py & echo         """  
        self._log(f"Searching for: {query}")  
        if not self.chunks:  
            print("Index is empty.")  
            return []  
  
        # 1. Keyword Search (BM25)  
        tokenized_query = query.lower().split(" ")  
        bm25_scores = self.bm25.get_scores(tokenized_query)  
        # Normalize BM25 scores (0-1)  
        if bm25_scores.max()  
            bm25_scores = bm25_scores / bm25_scores.max() 
  
        # 2. Vector Search  
        # Embed query  
        query_vectors = self.embedder.generate_embeddings([{"text": query, "metadata": {}}])  
        if not query_vectors:  
            print("Failed to embed query.")  
            vector_scores = np.zeros(len(self.chunks))  
        else:  
            query_vec = np.array(query_vectors[0].embedding)  
ECHO is on.
            # Normalize query  
            norm_q = np.linalg.norm(query_vec)  
            if norm_q  
                query_vec = query_vec / norm_q  
ECHO is on.
            # Normalize doc vectors  
            norm_docs = np.linalg.norm(self.vectors, axis=1)  
            norm_docs[norm_docs == 0] = 1  
ECHO is on.
            normalized_vectors = self.vectors / norm_docs[:, np.newaxis]  
ECHO is on.
            vector_scores = np.dot(normalized_vectors, query_vec)  
            vector_scores = np.clip(vector_scores, 0, 1) 
  
        # 3. Combine scores  
        hybrid_scores = (1 - alpha) * bm25_scores + alpha * vector_scores  
ECHO is on.
        # 4. Apply Filters (Metadata)  
        if filters:  
            for i, chunk in enumerate(self.chunks):  
                metadata = chunk.get("metadata", {})  
                match = True  
                for key, value in filters.items():  
                    if not value:   
                        continue  
ECHO is on.
                    if key not in metadata:  
                        match = False  
                        break  
ECHO is on.
                    meta_val = metadata[key]  
                    if isinstance(value, list):  
                        if meta_val not in value:  
                            match = False  
                            break  
                    else:  
                        if meta_val != value:  
                            match = False  
                            break  
ECHO is on.
                if not match:  
                    hybrid_scores[i] = -1.0 # Exclude 
  
        # 5. Apply Content Constraints (Must-Have Terms)  
        if must_have_terms:  
            # Pre-compute lower case terms  
            terms_lower = [t.lower() for t in must_have_terms]  
            for i, chunk in enumerate(self.chunks):  
                # Skip if already excluded  
                if hybrid_scores[i] < 0:  
                    continue  
ECHO is on.
                text_lower = chunk["text"].lower()  
                has_term = False  
                for term in terms_lower:  
                    if term in text_lower:  
                        has_term = True  
                        break  
ECHO is on.
                if not has_term:  
                    hybrid_scores[i] = -1.0 # Exclude 
