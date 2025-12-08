from typing import Dict, Any, Optional
from google.cloud import firestore
from crawler import config
import hashlib

class DocStore:
    def __init__(self, collection_name: str = '3gpp_knowledge_base'):
        # Firestore client requires project ID; database defaults to (default)
        self.db = firestore.Client(project=config.PROJECT_ID)
        self.collection = self.db.collection(collection_name)
        print(f'Connected to Firestore: {collection_name}')

    def upsert_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        doc_ref = self.collection.document(doc_id)
        # Use merge=True just in case, though set() overwrites by default
        doc_ref.set({
            'text': text,
            'metadata': metadata,
            'id': doc_id
        }, merge=True)

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.collection.document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    def generate_id(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
