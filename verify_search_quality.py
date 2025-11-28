import os
import sys
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.claim_processor import ClaimProcessor
from brain.search import HybridSearcher

def verify_search_quality():
    print("=== Verifying Search Quality Fixes ===")
    
    # 1. Verify Claim Processor
    print("\n[Test 1] Claim Processor Logic")
    processor = ClaimProcessor()
    
    # Test Claim with "device-to-device" (should trigger Sidelink constraint)
    claim = "A method for device-to-device communication using a sidelink control channel."
    print(f"Claim: {claim}")
    
    query, constraints = processor.process_claim(claim)
    print(f"Processed Query: {query}")
    print(f"Constraints: {constraints}")
    
    # Checks
    if "SIDELINK" in constraints or "sidelink" in constraints:
        print("PASS: 'Sidelink' constraint found.")
    else:
        print("FAIL: 'Sidelink' constraint missing.")
        
    if "PSCCH" in query:
         print("PASS: 'PSCCH' found in query (Acronym expansion).")
    else:
         print("FAIL: 'PSCCH' missing from query.")
         
    # Check Boosting (repetition)
    if query.count("SIDELINK") > 5 or query.count("sidelink") > 5:
        print("PASS: 'Sidelink' term appears boosted (repeated).")
    else:
        print("FAIL: 'Sidelink' term not boosted.")

    # 2. Verify Searcher Filtering
    print("\n[Test 2] Searcher Content Filtering")
    searcher = HybridSearcher()
    
    # Inject a dummy chunk for testing
    dummy_chunk = {
        "text": "This is a specification regarding NR Sidelink communication and V2X services.",
        "embedding": [0.0] * 768, # Dummy embedding
        "metadata": {"title": "Dummy Sidelink Doc", "source": "Test", "type": "TDoc"}
    }
    searcher.chunks.append(dummy_chunk)
    # Re-init BM25 with new corpus
    searcher.corpus.append(dummy_chunk['text'].lower().split(" "))
    from rank_bm25 import BM25Okapi
    searcher.bm25 = BM25Okapi(searcher.corpus)
    # Update vectors (append dummy zero vector)
    import numpy as np
    if len(searcher.vectors) > 0:
        searcher.vectors = np.vstack([searcher.vectors, np.zeros((1, 768))])
    else:
        searcher.vectors = np.zeros((1, 768))
        
    print("Injected dummy Sidelink document.")
    
    # Case A: Search with matching constraint
    print("\nCase A: Search with constraint ['sidelink']")
    results_a = searcher.search("sidelink", top_k=5, must_have_terms=["sidelink"])
    
    found_dummy = False
    for res in results_a:
        if res['chunk']['text'] == dummy_chunk['text']:
            found_dummy = True
            break
            
    if found_dummy:
        print("PASS: Dummy document returned.")
    else:
        print("FAIL: Dummy document NOT returned.")
        
    # Case B: Search with non-matching constraint
    print("\nCase B: Search with constraint ['foobar']")
    results_b = searcher.search("sidelink", top_k=5, must_have_terms=["foobar"])
    
    found_dummy_b = False
    for res in results_b:
        if res['chunk']['text'] == dummy_chunk['text']:
            found_dummy_b = True
            break
            
    if not found_dummy_b:
        print("PASS: Dummy document correctly excluded.")
    else:
        print("FAIL: Dummy document returned despite mismatching constraint.")

if __name__ == "__main__":
    verify_search_quality()
