import os
import sys
import glob
import zipfile

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from refinery.parser import TDocParser

def verify_classifier():
    print("Verifying Document Classifier...")
    
    # Use the samples we have
    source_dir = "data/samples/RAN1_104e"
    files = glob.glob(os.path.join(source_dir, "*.zip"))
    
    if not files:
        print("No sample files found.")
        return

    for file_path in files[:5]:
        print(f"\nProcessing {os.path.basename(file_path)}...")
        try:
            target_file = file_path
            # Unzip logic (same as pipeline)
            if file_path.endswith(".zip"):
                extract_dir = os.path.splitext(file_path)[0]
                if not os.path.exists(extract_dir):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                docx_files = glob.glob(os.path.join(extract_dir, "*.docx"))
                if docx_files:
                    target_file = docx_files[0]
                else:
                    print("  No .docx found.")
                    continue

            parser = TDocParser(target_file)
            result = parser.parse()
            
            if result:
                doc_type = result["metadata"].get("type", "Unknown")
                title = result["metadata"].get("title", "No Title")
                print(f"  Title: {title}")
                print(f"  Classified as: {doc_type}")
            else:
                print("  Failed to parse.")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    verify_classifier()
