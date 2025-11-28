from typing import List, Dict, Any
import re

class ChunkingStrategy:
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks a document into smaller pieces.
        document: Dict containing 'content', 'metadata', etc.
        """
        text = document.get('content', '')
        metadata = document.get('metadata', {})
        
        if not text:
            return []

        chunks = []
        
        # 1. Split by paragraphs (double newline)
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # If adding this paragraph exceeds chunk size, save current chunk
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "metadata": metadata
                    })
                    # Start new chunk with overlap (simple implementation: just last n chars)
                    # For now, no overlap for simplicity, or just simple carry over
                    current_chunk = para
                else:
                    # Paragraph itself is huge, force split it?
                    # For now, just accept it as a large chunk
                    chunks.append({
                        "text": para,
                        "metadata": metadata
                    })
                    current_chunk = ""
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add remaining
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": metadata
            })
            
        return chunks

if __name__ == "__main__":
    # Test
    doc = {
        "content": "Para 1.\n\nPara 2 is longer.\n\nPara 3.",
        "metadata": {"title": "Test"}
    }
    chunker = ChunkingStrategy(chunk_size=20)
    print(chunker.chunk_document(doc))
