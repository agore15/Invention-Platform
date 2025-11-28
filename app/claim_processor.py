import json
import re
import os
import sys
import spacy
from thefuzz import process
from typing import Tuple, List

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("DEBUG: Loaded updated ClaimProcessor with Search Quality Fixes")

class ClaimProcessor:
    def __init__(self, acronyms_file: str = "refinery/acronyms.json", custom_acronyms_file: str = "refinery/custom_acronyms.json"):
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
        
        # Common patent legalese phrases (Regex for multi-word)
        # Use word boundaries \b to avoid partial matches
        self.legalese_phrases = [
            r"\bcomprising\b", r"\bconsisting of\b", r"\bwherein\b", r"\bcharacterized in that\b",
            r"\bsaid\b", r"\bthe method of claim \d+\b", r"\baccording to claim \d+\b",
            r"\ba plurality of\b", r"\bconfigured to\b", r"\badapted to\b", r"\bmethod for\b",
            r"\bsystem for\b", r"\bapparatus for\b", r"\bmethod\b", r"\bsystem\b", r"\bapparatus\b"
        ]

        # Domain Triggers and Constraints
        # If key is found in claim, at least one of the values must be in the document
        self.domain_constraints = {
            "SIDELINK": ["sidelink", "v2x", "pc5", "prose", "device-to-device", "d2d"],
            "D2D": ["sidelink", "v2x", "pc5", "prose", "device-to-device", "d2d"],
            "V2X": ["sidelink", "v2x", "pc5", "prose", "device-to-device", "d2d"],
            "PC5": ["sidelink", "v2x", "pc5", "prose", "device-to-device", "d2d"],
            "PROSE": ["sidelink", "v2x", "pc5", "prose", "device-to-device", "d2d"]
        }

        # Terms to Boost (Weight 10.0)
        self.boost_terms = [
            "SIDELINK", "PSCCH", "PSSCH", "PSBCH", "V2X", "PC5", "PROSE", "D2D", "DEVICE-TO-DEVICE"
        ]

    def _load_acronyms(self, path: str):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.acronyms = json.load(f)
        else:
            print(f"Warning: Acronyms file {path} not found.")

    def _load_custom_acronyms(self, path: str):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                custom = json.load(f)
                # Merge custom into main, overwriting if exists
                self.acronyms.update(custom)
                print(f"Loaded {len(custom)} custom acronyms.")
        else:
            print(f"Warning: Custom acronyms file {path} not found.")

    def process_claim(self, claim_text: str) -> Tuple[str, List[str]]:
        """
        Processes a raw patent claim into a search query.
        Returns: (boosted_query_string, must_have_constraints)
        """
        # print(f"DEBUG: Original: {claim_text}")
        
        # 1. Strip Legalese Phrases (Regex)
        cleaned_text = claim_text.lower()
        for pattern in self.legalese_phrases:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        
        # 1.5. Multi-word Acronym/Phrase Replacement (from custom acronyms)
        # We prioritize custom acronyms for phrase replacement
        # Sort by length (descending) to match longest phrases first
        # This is a simple implementation; for production, use a Trie or Aho-Corasick
        custom_phrases = [k for k in self.acronyms.keys() if " " in k or "-" in k]
        custom_phrases.sort(key=len, reverse=True)
        
        for phrase in custom_phrases:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            if pattern.search(cleaned_text):
                cleaned_text = pattern.sub(self.acronyms[phrase], cleaned_text)
        
        # 2. SpaCy Processing (Tokenization & Stopword Removal)
        doc = self.nlp(cleaned_text)
        
        # Keep only non-stop words
        tokens = []
        for token in doc:
            if token.is_stop or token.is_punct or token.is_space:
                continue
            # Explicitly filter common articles if spaCy misses them
            if token.text.lower() in ["a", "an", "the"]:
                continue
                
            tokens.append(token.text)
        
        # 3. Acronym Injection & Domain Analysis
        final_tokens = []
        constraints = set()
        
        for token in tokens:
            final_tokens.append(token)
            
            upper_token = token.upper()
            
            # Check for Domain Constraints
            if upper_token in self.domain_constraints:
                for c in self.domain_constraints[upper_token]:
                    constraints.add(c)
            
            # Check for Boosting
            if upper_token in self.boost_terms:
                # Repeat the term 10 times to boost BM25 score
                for _ in range(10):
                    final_tokens.append(token)
            
            # Check for acronym
            # Exact Match
            if upper_token in self.acronyms:
                acronym_val = self.acronyms[upper_token]
                final_tokens.append(f"({acronym_val})")
                
                # Check constraints/boosting on the expanded acronym too
                # Simple check: if expanded contains boost terms
                for term in self.boost_terms:
                    if term in acronym_val.upper():
                         for _ in range(10):
                            final_tokens.append(term.lower())

            else:
                # Fuzzy Match (only if length > 2 to avoid noise)
                if len(upper_token) > 2:
                    # Get best match with score > 80
                    match = process.extractOne(upper_token, self.acronyms.keys(), score_cutoff=80)
                    if match:
                        acronym, score = match
                        acronym_val = self.acronyms[acronym]
                        final_tokens.append(f"({acronym_val})")
                        
                        # Check constraints/boosting on the expanded acronym
                        for term in self.boost_terms:
                            if term in acronym_val.upper():
                                for _ in range(10):
                                    final_tokens.append(term.lower())

        final_query = " ".join(final_tokens)
        return final_query, list(constraints)

if __name__ == "__main__":
    # Test
    processor = ClaimProcessor()
    claim = "A method comprising a UE configured to transmit a PUSCH to a gNB via device-to-device communication."
    print(f"Original: {claim}")
    query, constraints = processor.process_claim(claim)
    print(f"Processed: {query}")
    print(f"Constraints: {constraints}")
