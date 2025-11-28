import json
import re
import os
import sys
import spacy
from thefuzz import process

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("DEBUG: Loaded updated ClaimProcessor")

class ClaimProcessor:
    def __init__(self, acronyms_file: str = "refinery/acronyms.json"):
        self.acronyms = {}
        self._load_acronyms(acronyms_file)
        
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

    def _load_acronyms(self, path: str):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.acronyms = json.load(f)
        else:
            print(f"Warning: Acronyms file {path} not found.")

    def process_claim(self, claim_text: str) -> str:
        """
        Processes a raw patent claim into a search query.
        1. Strips legalese (Regex + SpaCy Stopwords).
        2. Injects/Expands acronyms (Exact + Fuzzy).
        """
        # print(f"DEBUG: Original: {claim_text}")
        
        # 1. Strip Legalese Phrases (Regex)
        cleaned_text = claim_text.lower()
        for pattern in self.legalese_phrases:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)
        
        # print(f"DEBUG: After Regex: {cleaned_text}")
        
        # Normalize whitespace
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        # print(f"DEBUG: After Normalize: {cleaned_text}")
        
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
        
        # print(f"DEBUG: Tokens after SpaCy: {tokens}")
        
        # 3. Acronym Injection
        final_tokens = []
        for token in tokens:
            final_tokens.append(token)
            
            # Check for acronym
            upper_token = token.upper()
            
            # Exact Match
            if upper_token in self.acronyms:
                final_tokens.append(f"({self.acronyms[upper_token]})")
            else:
                # Fuzzy Match (only if length > 2 to avoid noise)
                if len(upper_token) > 2:
                    # Get best match with score > 80
                    match = process.extractOne(upper_token, self.acronyms.keys(), score_cutoff=80)
                    if match:
                        acronym, score = match
                        final_tokens.append(f"({self.acronyms[acronym]})")

        final_query = " ".join(final_tokens)
        return final_query

if __name__ == "__main__":
    # Test
    processor = ClaimProcessor()
    claim = "A method comprising a UE configured to transmit a PUSCH to a gNB."
    print(f"Original: {claim}")
    print(f"Processed: {processor.process_claim(claim)}")
