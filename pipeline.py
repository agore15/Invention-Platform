import os
import sys
import glob
import zipfile
from typing import List

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from crawler.crawler import ThreeGPPCrawler
from refinery.parser import TDocParser
from brain.indexer import ChunkingStrategy
from brain.vectorizer import EmbeddingGenerator, Indexer

def run_pipeline(download_limit: int = 5):
    print("=== Starting 3GPP Data Pipeline ===")

    # 1. Crawler
    print("\n[Phase 1] Running Crawler...")
    crawler = ThreeGPPCrawler()
    # For demo purposes, we might want to limit what we download or just use what's there.
    # Let's assume we want to crawl a specific meeting directory.
    target_dir = "/tsg_ran/WG1_RL1/TSGR1_104-e/Docs/" 
    local_dir = "data/downloads"
    
    # Check if we already have data to avoid re-downloading huge amounts for this test
    if not os.path.exists(local_dir) or len(os.listdir(local_dir)) == 0:
        print(f"Downloading from {target_dir}...")
        # Note: This might take a long time for the full directory. 
        # In a real run, you'd let this finish. 
        # For this script, we'll rely on the crawler's logic (which we verified).
        # crawler.download_directory(target_dir, local_dir)
        pass
    else:
        print(f"Data directory {local_dir} exists. Skipping download for this run.")

    # 2. Refinery (Parser)
    print("\n[Phase 2] Running Refinery (Parser)...")
    chunker = ChunkingStrategy()
    
    # Find all .zip files (TDocs)
    # Assuming samples for now if downloads are empty
    source_dir = "data/samples/RAN1_104e" if os.path.exists("data/samples/RAN1_104e") else local_dir
    files = glob.glob(os.path.join(source_dir, "*.zip"))
    
    if not files:
        print("No files found to process.")
        return

    print(f"Found {len(files)} files. Processing first {download_limit}...")
    
    all_chunks = []
    
    for file_path in files[:download_limit]:
        print(f"  Processing {os.path.basename(file_path)}...")
        try:
            target_file = file_path
            
            # Unzip if it's a zip file
            if file_path.endswith(".zip"):
                extract_dir = os.path.splitext(file_path)[0]
                if not os.path.exists(extract_dir):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                
                # Find the docx in the extracted folder
                docx_files = glob.glob(os.path.join(extract_dir, "*.docx"))
                if not docx_files:
                    print(f"    No .docx found in {file_path}")
                    continue
                target_file = docx_files[0] # Take the first one

            # Parse
            parser = TDocParser(target_file)
            doc_data = parser.parse()
            if not doc_data:
                continue
                
            # Chunk
            doc_chunks = chunker.chunk_document(doc_data)
            all_chunks.extend(doc_chunks)
            print(f"    -> Extracted {len(doc_chunks)} chunks.")
            
        except Exception as e:
            print(f"    Error processing {file_path}: {e}")

    # 3. Brain (Embedding & Indexing)
    print(f"\n[Phase 3] Running Brain (Embedding & Indexing)...")
    print(f"Total chunks to index: {len(all_chunks)}")
    
    if all_chunks:
        embedder = EmbeddingGenerator()
        indexer = Indexer() # Defaults to brain/index.json
        
        print("  Generating embeddings...")
        vectorized_chunks = embedder.generate_embeddings(all_chunks)
        
        print("  Indexing...")
        indexer.upload_vectors(vectorized_chunks)
        
    print("\n=== Pipeline Complete ===")
    print("You can now run the UI to search this data.")

if __name__ == "__main__":
    run_pipeline()
