import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from brain.search import HybridSearcher

class SearchEngine:
    def __init__(self):
        # Initialize the real HybridSearcher
        # Assuming the index is at ../brain/index.json
        index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain', 'index.json')
        self.searcher = HybridSearcher(index_path)

    def search(self, query, filters=None):
        print(f'Searching for: {query} with filters: {filters}')
        # Perform actual search
        try:
            results = self.searcher.search(query, top_k=20, alpha=0.1)
        except Exception as e:
            print(f'Search failed: {e}')
            return []
        
        # Map results to the expected format
        formatted_results = []
        for r in results:
            # HybridSearcher returns {'chunk': {...}, 'score': ...}
            chunk = r['chunk']
            formatted_results.append({
                'id': 'DOC-' + str(hash(chunk['text']))[:8],
                'text': chunk['text'],
                'metadata': chunk.get('metadata', {})
            })
            
        return formatted_results

    def generate_answer(self, results, query):
        if not results:
            return 'No relevant documents found.'
            
        # Construct a summary from the top results
        answer = f'Based on the search results, here is an answer regarding \'{query}\':\n\n'
        
        # Summarize the top 3 results
        for i, r in enumerate(results[:3]):
            text_preview = r['text'][:200].replace('\n', ' ') + '...'
            source = r['metadata'].get('source', 'Unknown Source')
            title = r['metadata'].get('title', 'Untitled')
            answer += f'**{i+1}. {title} ({source})**\n{text_preview}\n\n'
            
        answer += '**Sources:**\n'
        for r in results:
             source = r['metadata'].get('source', 'Unknown Source')
             title = r['metadata'].get('title', 'Untitled')
             answer += f'- {title} ({source})\n'
             
        return answer
