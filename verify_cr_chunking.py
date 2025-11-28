import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain.indexer import ChunkingStrategy

def verify_cr_chunking():
    print("Verifying CR Chunking Logic...")
    
    chunker = ChunkingStrategy()
    
    # Mock Document with CR fields
    doc = {
        "content": "This is the body text of the CR.",
        "metadata": {"title": "Test CR", "type": "CR"},
        "cr_fields": {
            "reason_for_change": "The current specification is ambiguous.",
            "summary_of_change": "Clarified the procedure for beam failure recovery."
        }
    }
    
    chunks = chunker.chunk_document(doc)
    
    print(f"Generated {len(chunks)} chunks.")
    
    cr_chunks = [c for c in chunks if c["metadata"].get("section") == "CR Cover Sheet"]
    print(f"Found {len(cr_chunks)} CR Cover Sheet chunks.")
    
    for c in cr_chunks:
        print(f"  - Text: {c['text']}")
        print(f"  - Weight: {c['metadata'].get('weight')}")
        
    if len(cr_chunks) == 2:
        print("PASS: Correctly extracted CR fields as chunks.")
    else:
        print("FAIL: Did not extract CR fields correctly.")

if __name__ == "__main__":
    verify_cr_chunking()
