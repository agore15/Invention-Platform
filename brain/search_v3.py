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
