from google.cloud import firestore
import logging

try:
    db = firestore.Client(project='still-manifest-478014-c1')
    collection_name = '3gpp_knowledge_base'
    doc_id = '07404070e5d114c0d8a4a04a8b01dcc0'
    
    doc_ref = db.collection(collection_name).document(doc_id)
    doc = doc_ref.get()
    
    if doc.exists:
        print(f"Success! Document {doc_id} found in Firestore.")
        print(f"Content Preview: {doc.to_dict().get('text', '')[:50]}...")
    else:
        print(f"Failure: Document {doc_id} NOT found in Firestore.")
        print("This means Vector Search IDs do not match Firestore IDs (Dataflow vs Local mismatch).")

except Exception as e:
    print(f"Error: {e}")
