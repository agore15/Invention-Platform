import re
from typing import Dict, Optional

class DocumentClassifier:
    """
    Classifies 3GPP documents into types: CR, LS, WID, TDoc.
    """
    
    def classify(self, text: str, metadata: Dict[str, str]) -> str:
        """
        Determines the document type based on text content and metadata.
        
        Args:
            text: The full text content of the document.
            metadata: Extracted metadata (title, source, etc.).
            
        Returns:
            str: One of "CR", "LS", "WID", "TDoc", or "Unknown".
        """
        text_lower = text.lower()[:2000] # Check first 2000 chars
        title = metadata.get("title", "").lower()
        
        # 1. Check for Change Request (CR)
        if "change request" in text_lower or "change request" in title:
            return "CR"
        if "reason for change" in text_lower and "summary of change" in text_lower:
            return "CR"
            
        # 2. Check for Liaison Statement (LS)
        if "liaison statement" in text_lower or "liaison statement" in title:
            return "LS"
        if re.search(r"\bls\b", title): # "LS" as a whole word in title
            return "LS"
            
        # 3. Check for Work Item Description (WID)
        if "work item description" in text_lower or "work item description" in title:
            return "WID"
            
        # 4. Default to TDoc (Discussion Paper)
        # Most R1-xxxxx documents are TDocs if not the above.
        return "TDoc"
