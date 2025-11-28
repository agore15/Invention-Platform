import json
import os
import sys
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain.vectorizer import EmbeddingGenerator

def inject_data():
    index_file = "brain/index.json"
    
    if not os.path.exists(index_file):
        print(f"Error: {index_file} not found.")
        return

    print(f"Loading {index_file}...")
    with open(index_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Current index size: {len(data)} chunks.")
    
    # Sample Sidelink Data
    new_docs = [
        {
            "text": "Discussion on NR Sidelink resource allocation mode 2. The UE autonomously selects resources from the configured resource pool. Sensing is performed to identify available resources. The PSCCH transmits the SCI which schedules the PSSCH.",
            "metadata": {
                "title": "NR Sidelink Resource Allocation",
                "source": "Qualcomm",
                "type": "TDoc",
                "status": "Draft"
            }
        },
        {
            "text": "V2X services require low latency and high reliability. PC5 interface is used for device-to-device communication. Groupcast and unicast are supported in NR V2X. HARQ feedback is enabled for unicast.",
            "metadata": {
                "title": "NR V2X Enhancements",
                "source": "Huawei",
                "type": "TDoc",
                "status": "Agreed"
            }
        },
        {
            "text": "ProSe (Proximity Services) allows UEs to discover each other and communicate directly. This is essential for public safety applications. Sidelink control information is carried on PSCCH.",
            "metadata": {
                "title": "ProSe Overview",
                "source": "Nokia",
                "type": "TDoc",
                "status": "Discussed"
            }
        }
    ]
    
    print("Generating embeddings for new docs...")
    embedder = EmbeddingGenerator()
    
    # Generate embeddings
    # The embedder expects a list of dicts with 'text' and 'metadata'
    # It returns a list of objects with an 'embedding' attribute
    embedded_docs = embedder.generate_embeddings(new_docs)
    
    for i, doc in enumerate(new_docs):
        # Add embedding to the doc dict
        doc['embedding'] = embedded_docs[i].embedding
        data.append(doc)
        
    print(f"New index size: {len(data)} chunks.")
    
    print(f"Saving to {index_file}...")
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print("Injection complete.")

if __name__ == "__main__":
    inject_data()
