from typing import List, Dict, Any
import re

class ChunkingStrategy:
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = document.get('content', '')
        metadata = document.get('metadata', {})
        
        if not text:
            return []

        chunks = []
        
        # 1. Split by paragraphs (double newline)
        paragraphs = text.split('\n\n')
        
        # Fallback: If text is long but no double newlines, split by single newline
        if len(paragraphs) == 1 and len(text) > self.chunk_size:
            paragraphs = text.split('\n')
        
        current_chunk = ''
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'metadata': metadata
                    })
                    current_chunk = para
                else:
                    chunks.append({
                        'text': para,
                        'metadata': metadata
                    })
                    current_chunk = ''
            else:
                if current_chunk:
                    current_chunk += '\n\n' + para
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'metadata': metadata
            })
            
        return chunks
