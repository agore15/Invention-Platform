import streamlit as st
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.claim_processor import ClaimProcessor
from brain.search import HybridSearcher

# Initialize components (cache to avoid reloading on every interaction)
@st.cache_resource
def load_components():
    processor = ClaimProcessor()
    searcher = HybridSearcher()
    return processor, searcher

processor, searcher = load_components()

st.set_page_config(page_title="3GPP Claim-to-Search", layout="wide")

st.title("3GPP Claim-to-Search Engine")
st.markdown("Enter a patent claim below to find relevant 3GPP TDocs.")

# Input
claim_text = st.text_area("Patent Claim", height=150, placeholder="A method comprising a UE configured to...")

col1, col2 = st.columns([1, 4])
with col1:
    search_btn = st.button("Search", type="primary")

if search_btn and claim_text:
    with st.spinner("Processing Claim..."):
        # 1. Process Claim
        query = processor.process_claim(claim_text)
        
        st.subheader("Processed Query")
        st.info(query)
        
        # 2. Search
        results = searcher.search(query, top_k=10)
        
        st.subheader(f"Top {len(results)} Results")
        
        if not results:
            st.warning("No results found.")
        else:
            for i, res in enumerate(results):
                chunk = res['chunk']
                score = res['score']
                metadata = chunk.get('metadata', {})
                
                with st.expander(f"{i+1}. {metadata.get('title', 'Untitled')} (Score: {score:.4f})"):
                    st.markdown(f"**Source:** {metadata.get('source', 'Unknown')}")
                    st.markdown(f"**Relevance Score:** {score:.4f} (BM25: {res['bm25_score']:.4f}, Vector: {res['vector_score']:.4f})")
                    st.markdown("---")
                    st.markdown(chunk['text'])

elif search_btn:
    st.error("Please enter a claim.")
