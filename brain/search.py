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
    def __init__(self, index_file: str = 'brain/index.json'):
        self.index_file = index_file
        self.bm25 = None
        self.chunks = []
        self.corpus = []
        self.vectors = [] # Numpy array of embeddings
        self.embedder = EmbeddingGenerator() # For query embedding

        self._load_index()

    def _log(self, msg: str):
        with open('debug_search.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()}: {msg}\n')

    def _load_index(self):
        if not os.path.exists(self.index_file):
            print(f'Warning: Index file {self.index_file} not found.')
            return

        print(f'Loading index from {self.index_file}...')
        with open(self.index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.chunks = data
        self.corpus = [chunk['text'].lower().split(' ') for chunk in data]
        self.bm25 = BM25Okapi(self.corpus)
        # Load vectors into numpy array
        embeddings = [chunk['embedding'] for chunk in data]
        if embeddings:
            self.vectors = np.array(embeddings)
        else:
            self.vectors = np.array([])
        print(f'Loaded {len(self.chunks)} chunks.')

    def _extract_phrases(self, query: str) -> List[str]:
        # Extracts quoted phrases from the query and normalizes them.
        return re.findall(r'"(.+?)"', query)

    def search(self, query: str, top_k: int = 5, alpha: float = 0.5, filters: Dict[str, Any] = None, must_have_terms: List[str] = None) -> List[Dict[str, Any]]:
        '''
        Performs hybrid search with optional metadata filtering and content constraints.
        alpha: Weight for vector search (0.0 to 1.0). 1.0 = pure vector, 0.0 = pure keyword.
        filters: Dictionary of metadata filters (e.g., {'type': 'CR', 'source': 'Qualcomm'}).
        must_have_terms: List of strings. If provided, returned docs MUST contain at least one of these terms (case-insensitive).
        '''
        self._log(f'Searching for: {query}')
        if not self.chunks:
            print('Index is empty.')
            return []

        # 1. Keyword Search (BM25)
        tokenized_query = query.lower().split(' ')
        bm25_scores = self.bm25.get_scores(tokenized_query)
        # Normalize BM25 scores (0-1)
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max()

        # 2. Vector Search
        # Embed query
        query_vectors = self.embedder.generate_embeddings([{'text': query, 'metadata': {}}])
        if not query_vectors:
            print('Failed to embed query.')
            vector_scores = np.zeros(len(self.chunks))
        else:
            query_vec = np.array(query_vectors[0].embedding)
            # Normalize query
            norm_q = np.linalg.norm(query_vec)
            if norm_q > 0:
                query_vec = query_vec / norm_q
            # Normalize doc vectors
            norm_docs = np.linalg.norm(self.vectors, axis=1)
            norm_docs[norm_docs == 0] = 1
            normalized_vectors = self.vectors / norm_docs[:, np.newaxis]
            vector_scores = np.dot(normalized_vectors, query_vec)
            vector_scores = np.clip(vector_scores, 0, 1)

        # 3. Combine scores
        hybrid_scores = (1 - alpha) * bm25_scores + alpha * vector_scores
        # 4. Apply Filters (Metadata)
        if filters:
            for i, chunk in enumerate(self.chunks):
                metadata = chunk.get('metadata', {})
                match = True
                for key, value in filters.items():
                    if not value:
                        continue
                    if key not in metadata:
                        match = False
                        break
                    meta_val = metadata[key]
                    if isinstance(value, list):
                        if meta_val not in value:
                            match = False
                            break
                    else:
                        if meta_val != value:
                            match = False
                            break
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
                text_lower = chunk['text'].lower()
                has_term = False
                for term in terms_lower:
                    if term in text_lower:
                        has_term = True
                        break
                if not has_term:
                    hybrid_scores[i] = -1.0 # Exclude

        # 6. Phrase Boosting
        phrases = self._extract_phrases(query)
        if phrases:
            phrase_boost_scores = np.zeros(len(self.chunks))
            boost_count = 0
            for i, chunk in enumerate(self.chunks):
                # Skip if excluded
                if hybrid_scores[i] < 0:
                    continue
                text_lower = chunk['text'].lower()
                for phrase in phrases:
                    if phrase.lower() in text_lower:
                        phrase_boost_scores[i] += 1.0 # Significant boost
                        boost_count += 1
                        self._log(f'Boosted chunk {i} for phrase "{phrase}"')
            self._log(f'Total chunks boosted: {boost_count}')
            hybrid_scores += phrase_boost_scores

        # Get top K
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if hybrid_scores[idx] > -0.5: # Threshold to filter excluded
                results.append({
                    'chunk': self.chunks[idx],
                    'score': float(hybrid_scores[idx]),
                    'bm25_score': float(bm25_scores[idx]),
                    'vector_score': float(vector_scores[idx])
                })
        return results

    def get_unique_metadata_values(self, field: str) -> List[str]:
        # Returns a sorted list of unique values for a given metadata field.
        values = set()
        for chunk in self.chunks:
            val = chunk.get('metadata', {}).get(field)
            if val:
                values.add(val)
        return sorted(list(values))
