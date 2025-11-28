import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.claim_processor import ClaimProcessor
from brain.search import HybridSearcher

def verify_flow():
    print("Initializing components...")
    processor = ClaimProcessor()
    searcher = HybridSearcher()
    
    claim = "A method comprising a UE configured to transmit a PUSCH to a gNB."
    print(f"\nInput Claim: {claim}")
    
    # 1. Process
    query = processor.process_claim(claim)
    print(f"Processed Query: {query}")
    
    # 2. Search
    print("\nSearching...")
    results = searcher.search(query, top_k=5)
    
    print(f"\nFound {len(results)} results.")
    for i, res in enumerate(results):
        print(f"{i+1}. Score: {res['score']:.4f} | Text: {res['chunk']['text'][:50]}...")

if __name__ == "__main__":
    verify_flow()
