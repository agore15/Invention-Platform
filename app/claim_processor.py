import json
import re
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ClaimProcessor:
    def __init__(self, acronyms_file: str = "refinery/acronyms.json"):
        self.acronyms = {}
        self._load_acronyms(acronyms_file)
        
        # Common patent legalese to strip
        self.legalese = [
            r"comprising", r"consisting of", r"wherein", r"characterized in that",
            r"said", r"the method of claim \d+", r"according to claim \d+",
            r"a plurality of", r"configured to", r"adapted to"
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
        1. Strips legalese.
        2. Injects/Expands acronyms.
        """
        # 1. Strip Legalese
        cleaned_text = claim_text.lower()
        for pattern in self.legalese:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        
        # 2. Acronym Injection (Simple expansion)
        # For every word, if it matches an acronym key, append the definition
        # or vice-versa. For search, maybe just appending the definition is good.
        
        # Tokenize
        words = cleaned_text.split()
        expanded_words = []
        
        # Common stopwords to ignore for acronym expansion
        stopwords = {"to", "a", "an", "the", "in", "on", "at", "by", "for", "of", "and", "or", "is", "are"}

        for word in words:
            # Remove punctuation for lookup
            clean_word = word.strip(".,;:()")
            
            # Skip stopwords
            if clean_word.lower() in stopwords:
                expanded_words.append(word)
                continue

            expanded_words.append(word)
            
            # Check upper case version for acronym lookup (keys are usually CAPS)
            upper_word = clean_word.upper()
            if upper_word in self.acronyms:
                # Inject definition
                definition = self.acronyms[upper_word]
                expanded_words.append(f"({definition})")
                
        final_query = " ".join(expanded_words)
        return final_query

if __name__ == "__main__":
    # Test
    processor = ClaimProcessor()
    claim = "A method comprising a UE configured to transmit a PUSCH to a gNB."
    print(f"Original: {claim}")
    print(f"Processed: {processor.process_claim(claim)}")
