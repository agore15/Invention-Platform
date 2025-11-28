import spacy
import json
import os
import re

class QueryProcessor:
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.nlp = None
            print("Warning: spaCy model not found. using basic split.")
            
        self.acronyms = self._load_acronyms()
        self.definition_to_acronym = self._build_reverse_lookup(self.acronyms)
        
        self.stop_words = {
            "plurality", "comprising", "said", "device", "method", "system", "apparatus",
            "configured", "adapted", "wherein", "thereof"
        }

    def _load_acronyms(self):
        # Path relative to application/query_processor.py -> ../refinery/acronyms.json
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "refinery", "acronyms.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def _build_reverse_lookup(self, acronyms):
        lookup = {}
        for acr, defn in acronyms.items():
            # Handle multiple definitions separated by ;
            parts = [d.strip() for d in defn.split(';')]
            for part in parts:
                if len(part) > 1: # Ignore single chars
                    lookup[part.lower()] = acr
        
        # Add manual overrides for testing if missing
        if "beam failure recovery" not in lookup:
            lookup["beam failure recovery"] = "BFR"
        if "beam failure detection" not in lookup:
            lookup["beam failure detection"] = "BFD"
            
        return lookup

    def process(self, query):
        # 1. Strip Legalese
        cleaned = self._strip_legalese(query)
        
        # 2. Inject Acronyms
        enriched = self._inject_acronyms(cleaned)
        
        return enriched

    def _strip_legalese(self, query):
        if self.nlp:
            doc = self.nlp(query)
            tokens = [token.text for token in doc if token.text.lower() not in self.stop_words]
            return " ".join(tokens)
        else:
            # Fallback
            words = query.split()
            return " ".join([w for w in words if w.lower() not in self.stop_words])

    def _inject_acronyms(self, query):
        # Sort definitions by length (descending) to match longest first
        sorted_defs = sorted(self.definition_to_acronym.keys(), key=len, reverse=True)
        
        enriched_query = query
        query_lower = query.lower()
        
        # We need to be careful not to double inject or inject inside existing words.
        # Simple approach: Iterate and replace.
        # Better approach: Regex with word boundaries.
        
        for defn in sorted_defs:
            if defn in query_lower:
                # Check if it's already followed by the acronym
                acr = self.definition_to_acronym[defn]
                
                # Check if (ACR) is already there
                if f"({acr})" not in enriched_query:
                     # Case insensitive replace
                     pattern = re.compile(re.escape(defn), re.IGNORECASE)
                     # We use the original case from the match if possible, but here we just title case the definition
                     # or keep it as is.
                     # Let's just replace the match with "Match (ACR)"
                     enriched_query = pattern.sub(lambda m: f"{m.group(0)} ({acr})", enriched_query)
                     
        return enriched_query

    def sanitize(self, query):
        """
        Sanitizes the query by extracting key terms and acronyms, 
        discarding the original natural language structure.
        """
        # 1. Strip Legalese (removes stop words and common patent terms)
        cleaned = self._strip_legalese(query)
        
        # 2. Inject Acronyms (adds (ACR) to definitions)
        enriched = self._inject_acronyms(cleaned)
        
        # 3. Tokenize and deduplicate
        # We want a list of significant tokens.
        # Since _inject_acronyms returns a string, we split it.
        # We might want to be more sophisticated here, but for now, 
        # splitting by whitespace and keeping unique tokens is a good start.
        tokens = list(set(enriched.split()))
        
        return tokens
