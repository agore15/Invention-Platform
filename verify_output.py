import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from application.query_processor import QueryProcessor
from application.search import SearchEngine

def test_stress_query():
    print('--- Testing Stress Query ---')
    query = 'Prior art for SCI Format 2-A used for Wake-Up Indication in NR V2X (Sidelink) with Distance-to-Rx based triggering.'
    
    # 1. Process Query
    processor = QueryProcessor()
    processed_query = processor.process(query)
    print(f'Processed Query: {processed_query}')
    
    # 2. Search
    engine = SearchEngine()
    results = engine.search(processed_query)
    
    # 3. Generate Answer
    answer = engine.generate_answer(results, processed_query)
    print(f'\nGenerated Answer:\n{answer}')
    
    # 4. Check for key terms in results
    found_212 = False
    found_sci_2a = False
    
    # SearchEngine.search returns a list of dicts (chunks)
    for result in results:
        text = result.get('text', '')
        metadata = result.get('metadata', {})
        source = metadata.get('source', '')
        
        if '38.212' in source:
            found_212 = True
        if 'Format 2-A' in text or 'Format 2-A' in str(metadata):
            found_sci_2a = True
            
    if found_212:
        print('\nSUCCESS: Found TS 38.212 in results.')
    else:
        print('\nFAILURE: Did not find TS 38.212 in results.')
        
    if found_sci_2a:
        print('SUCCESS: Found SCI Format 2-A in results.')
    else:
        print('FAILURE: Did not find SCI Format 2-A in results.')

if __name__ == '__main__':
    test_stress_query()
