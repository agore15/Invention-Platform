import sys
import os
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import zipfile
import json
from docx import Document
from crawler import config

class VocabularyBuilder:
    def __init__(self, vocabulary_zip_path: str):
        self.zip_path = vocabulary_zip_path
        self.extract_dir = os.path.dirname(vocabulary_zip_path)
        self.doc_path = None
        self.acronyms = {}
        # Manual overrides for terms known to be missing or critical
        self.manual_overrides = {
            "NR": "New Radio",
            "gNB": "gNodeB; Next Generation Node B",
            "eNB": "eNodeB; Evolved Node B",
            "UE": "User Equipment",
        }

    def extract_zip(self):
        """Extracts the vocabulary zip file."""
        print(f"Extracting {self.zip_path}...")
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.extract_dir)
            for name in zip_ref.namelist():
                if name.lower().endswith(".docx"):
                    self.doc_path = os.path.join(self.extract_dir, name)
                    print(f"Found Word document: {self.doc_path}")
                    break

    def parse_vocabulary(self):
        """Parses the vocabulary document to build the acronym dictionary."""
        if not self.doc_path or not os.path.exists(self.doc_path):
            print("No .docx file found to parse.")
            return

        print(f"Parsing {self.doc_path}...")
        doc = Document(self.doc_path)
        
        current_acronym = None
        
        for para in doc.paragraphs:
            raw_text = para.text
            if not raw_text.strip():
                continue
                
            parts = raw_text.split('\t')
            
            if len(parts) >= 2:
                acronym = parts[0].strip()
                definition = parts[1].strip()
                
                if len(parts) > 2:
                    definition = " ".join(p.strip() for p in parts[1:]).strip()

                if definition.isdigit():
                    continue
                
                if acronym:
                    current_acronym = acronym
                    self._add_acronym(acronym, definition)
                elif current_acronym:
                    self._add_acronym(current_acronym, definition)
        
        # Apply overrides
        print("Applying manual overrides...")
        for acr, defn in self.manual_overrides.items():
            if acr not in self.acronyms:
                self.acronyms[acr] = defn
            else:
                existing = self.acronyms[acr]
                existing_defs = [d.strip() for d in existing.split(';')]
                if defn not in existing_defs:
                    self.acronyms[acr] = f"{existing}; {defn}"

    def _add_acronym(self, acronym, definition):
        if not definition:
            return
        definition = definition.strip()
        if acronym in self.acronyms:
            existing = self.acronyms[acronym]
            existing_defs = [d.strip() for d in existing.split(';')]
            if definition not in existing_defs:
                self.acronyms[acronym] = f"{existing}; {definition}"
        else:
            self.acronyms[acronym] = definition

    def save_acronyms(self, output_path: str):
        """Saves the acronym dictionary to a JSON file."""
        print(f"Saving {len(self.acronyms)} acronyms to {output_path}...")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.acronyms, f, indent=4)

def build_vocabulary():
    zip_path = os.path.join(config.BASE_DOWNLOAD_DIR, "Specs", "21_series", "21.905", "21905-j00.zip")
    if not os.path.exists(zip_path):
        print(f"Error: Vocabulary file not found at {zip_path}")
        return

    builder = VocabularyBuilder(zip_path)
    builder.extract_zip()
    builder.parse_vocabulary()
    
    output_path = os.path.join("refinery", "acronyms.json")
    builder.save_acronyms(output_path)

if __name__ == "__main__":
    build_vocabulary()
