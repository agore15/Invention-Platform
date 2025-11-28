import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.claim_processor import ClaimProcessor

def verify_processor():
    print("Verifying SpaCy Claim Processor...")
    
    processor = ClaimProcessor()
    
    # Test Case 1: Legalese Stripping
    claim1 = "A method comprising a UE configured to transmit a PUSCH."
    print(f"\nClaim 1: {claim1}")
    result1 = processor.process_claim(claim1)
    print(f"Result 1: {result1}")
    
    # Expected: "ue (User Equipment) transmit pusch (Physical Uplink Shared Channel)"
    # "A", "method", "comprising", "a", "configured", "to", "a", "to" should be removed (stopwords or legalese)
    
    if "method" not in result1 and "comprising" not in result1:
        print("PASS: Legalese stripped.")
    else:
        print("FAIL: Legalese remaining.")

    # Test Case 2: Fuzzy Matching
    # "User Eqipment" (typo) -> Should match UE? 
    # Or "gNodeB" -> Should match gNB?
    # The current logic matches UPPER CASE words in the claim to keys in acronyms.json.
    # So we need to test if a slightly misspelled acronym works? 
    # Actually, the code does `upper_token` lookup.
    # If I have "gNBB" (typo), it might fuzzy match "gNB".
    
    claim2 = "The gNBB transmits a signal."
    print(f"\nClaim 2: {claim2}")
    result2 = processor.process_claim(claim2)
    print(f"Result 2: {result2}")
    
    if "(gNB)" in result2 or "(Next Generation Node B)" in result2: # Depending on acronyms.json content
         print("PASS: Fuzzy match successful.")
    else:
         print("FAIL: Fuzzy match failed.")

if __name__ == "__main__":
    verify_processor()
