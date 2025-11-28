import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain.search import HybridSearcher

def verify_filtering():
    print("Verifying Targeted Filtering...")
    
    searcher = HybridSearcher()
    
    if not searcher.chunks:
        print("Index is empty. Cannot verify filtering.")
        return

    # Test 1: Filter by Type (e.g., exclude LS)
    # First, find a type that exists
    types = searcher.get_unique_metadata_values("type")
    print(f"Available types: {types}")
    
    if not types:
        print("No types found in metadata.")
    else:
        target_type = types[0]
        print(f"\nTest 1: Filter for type='{target_type}'")
        
        filters = {"type": [target_type]}
        results = searcher.search("test", top_k=10, filters=filters)
        
        all_match = True
        for res in results:
            doc_type = res['chunk']['metadata'].get('type')
            if doc_type != target_type:
                print(f"FAIL: Found type '{doc_type}', expected '{target_type}'")
                all_match = False
                break
        
        if all_match and results:
            print(f"PASS: All {len(results)} results match type '{target_type}'.")
        elif not results:
            print("WARNING: No results found with filter (might be valid if query doesn't match).")
        else:
            print("FAIL: Type filter failed.")

    # Test 2: Filter by Source
    sources = searcher.get_unique_metadata_values("source")
    print(f"\nAvailable sources: {sources}")
    
    if sources:
        target_source = sources[0]
        print(f"\nTest 2: Filter for source='{target_source}'")
        
        filters = {"source": target_source}
        results = searcher.search("test", top_k=10, filters=filters)
        
        all_match = True
        for res in results:
            src = res['chunk']['metadata'].get('source')
            if src != target_source:
                print(f"FAIL: Found source '{src}', expected '{target_source}'")
                all_match = False
                break
        
        if all_match and results:
            print(f"PASS: All {len(results)} results match source '{target_source}'.")
        elif not results:
             print("WARNING: No results found with filter.")
        else:
            print("FAIL: Source filter failed.")

if __name__ == "__main__":
    verify_filtering()
