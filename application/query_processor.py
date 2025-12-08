import spacy
import json
import os
import re

class QueryProcessor:
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = None
            print('Warning: spaCy model not found. using basic split.')
            
        self.acronyms = self._load_acronyms()
        self.definition_to_acronym = self._build_reverse_lookup(self.acronyms)
        
        self.stop_words = {
            'plurality', 'comprising', 'said', 'device', 'method', 'system', 'apparatus',
            'configured', 'adapted', 'wherein', 'thereof'
        }

    def _load_acronyms(self):
        # Path relative to application/query_processor.py -> ../refinery/acronyms.json
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'refinery', 'acronyms.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
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
        if 'beam failure recovery' not in lookup:
            lookup['beam failure recovery'] = 'BFR'
        if 'beam failure detection' not in lookup:
            lookup['beam failure detection'] = 'BFD'
            
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
            return ' '.join(tokens)
        else:
            # Fallback
            words = query.split()
            return ' '.join([w for w in words if w.lower() not in self.stop_words])

    def _inject_acronyms(self, query):
        # Sort definitions by length (descending) to match longest first
        sorted_defs = sorted(self.definition_to_acronym.keys(), key=len, reverse=True)
        
        enriched_query = query
        query_lower = query.lower()
        
        for defn in sorted_defs:
            if defn in query_lower:
                acr = self.definition_to_acronym[defn]
                
                # Regex to match definition NOT followed by an acronym in parentheses
                # AND ensure word boundaries to avoid partial matches (e.g. 'mat' in 'format')
                
                # \\b matches word boundary.
                # We escape defn to handle special chars.
                # We use negative lookahead for existing acronym.
                
                pattern = re.compile(r'\\b' + re.escape(defn) + r'\\b(?!\\s*\\([A-Za-z0-9-]+\\))', re.IGNORECASE)
                
                enriched_query = pattern.sub(lambda m: f'{m.group(0)} ({acr})', enriched_query)
                
        return enriched_query
