import json
import re
import os
import sys
import spacy
from typing import Tuple, List

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("DEBUG: Loaded updated ClaimProcessor with Search Quality Fixes (Final V2)")

class ClaimProcessor:
    def __init__(self, acronyms_file: str = "refinery/acronyms_final.json", custom_acronyms_file: str = "refinery/custom_acronyms.json"):
        self.acronyms = {}
        self._load_acronyms(acronyms_file)
        self._load_custom_acronyms(custom_acronyms_file)
        
        # Load SpaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model...")
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        self.legalese_phrases = [
            r"\bcomprising\b", r"\bconsisting of\b", r"\bwherein\b", r"\bcharacterized in that\b",
            r"\bsaid\b", r"\bthe method of claim \d+\b", r"\baccording to claim \d+\b",
            r"\ba plurality of\b", r"\bconfigured to\b", r"\badapted to\b", r"\bmethod for\b",
            r"\bsystem for\b", r"\bapparatus for\b", r"\bmethod\b", r"\bsystem\b", r"\bapparatus\b"
        ]

        self.domain_constraints = {
            "SIDELINK": ["sidelink", "v2x", "pc5", "prose", "device-to-device", "d2d"],
            "D2D": ["sidelink", "v2x", "pc5", "prose", "device-to-device", "d2d"],
            "V2X": ["sidelink", "v2x", "pc5", "prose", "device-to-device", "d2d"],
            "PC5": ["sidelink", "v2x", "pc5", "prose", "device-to-device", "d2d"],
            "PROSE": ["sidelink", "v2x", "pc5", "prose", "device-to-device", "d2d"]
        }

        self.boost_terms = [
            "SIDELINK", "PSCCH", "PSSCH", "PSBCH", "V2X", "PC5", "PROSE", "D2D", "DEVICE-TO-DEVICE",
            "POLAR", "LDPC", "PUCCH", "PUSCH"
        ]

    def _load_acronyms(self, path: str):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.acronyms = json.load(f)
        else:
            print(f"Warning: Acronyms file {path} not found. Using empty dict.")

    def _load_custom_acronyms(self, path: str):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                custom = json.load(f)
                self.acronyms.update(custom)
        else:
            pass

    def process_claim(self, claim_text: str) -> Tuple[str, List[str]]:
        cleaned_text = claim_text.lower()
        for pattern in self.legalese_phrases:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)
        
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        
        # 1.5. Custom Phrase Replacement
        custom_phrases = [k for k in self.acronyms.keys() if " " in k or "-" in k]
        custom_phrases.sort(key=len, reverse=True)
        
        for phrase in custom_phrases:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            if pattern.search(cleaned_text):
                cleaned_text = pattern.sub(self.acronyms[phrase], cleaned_text)
        
        doc = self.nlp(cleaned_text)
        
        tokens = []
        for token in doc:
            if token.is_stop or token.is_punct or token.is_space:
                continue
            if token.text.lower() in ["a", "an", "the"]:
                continue
            tokens.append(token.text)
        
        final_tokens = []
        constraints = set()
        
        for token in tokens:
            final_tokens.append(token)
            
            upper_token = token.upper()
            
            if upper_token in self.domain_constraints:
                for c in self.domain_constraints[upper_token]:
                    constraints.add(c)
            
            if upper_token in self.boost_terms:
                for _ in range(5):
                    final_tokens.append(token)
            
            # Exact Match Only for Acronyms (using filtered dictionary)
            if upper_token in self.acronyms:
                acronym_val = self.acronyms[upper_token]
                # Only inject if definition is reasonable length
                if len(acronym_val) < 100:
                    final_tokens.append(f"({acronym_val})")
                
                for term in self.boost_terms:
                    if term in acronym_val.upper():
                         for _ in range(5):
                            final_tokens.append(term.lower())

        final_query = " ".join(final_tokens)
        return final_query, list(constraints)

if __name__ == "__main__":
    processor = ClaimProcessor()
    claim = "A method comprising a UE configured to transmit a PUSCH to a gNB via device-to-device communication."
    print(f"Original: {claim}")
    query, constraints = processor.process_claim(claim)
    print(f"Processed: {query}")
    print(f"Constraints: {constraints}")
