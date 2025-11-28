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

# Sidebar Filters
st.sidebar.header("Filters")

# 1. Document Type Filter
# Get available types from index
available_types = searcher.get_unique_metadata_values("type")
# Default: Exclude 'LS' if present, otherwise select all
default_types = [t for t in available_types if t != "LS"]
if not default_types and available_types:
    default_types = available_types

selected_types = st.sidebar.multiselect(
    "Document Type",
    options=available_types,
    default=default_types,
    help="Select document types to include. LS (Liaison Statements) are excluded by default."
)

# 2. Source Filter
available_sources = searcher.get_unique_metadata_values("source")
selected_source = st.sidebar.selectbox(
    "Source",
    options=["All"] + available_sources,
    help="Filter by source organization (e.g., Qualcomm, Huawei)."
)

# 3. Status Filter
available_statuses = searcher.get_unique_metadata_values("status")
selected_status = st.sidebar.selectbox(
    "Status",
    options=["All"] + available_statuses,
    help="Filter by document status (e.g., Agreed, Draft)."
)

# Construct Filters Dictionary
filters = {}
if selected_types:
    filters["type"] = selected_types

if selected_source != "All":
    filters["source"] = selected_source

if selected_status != "All":
    filters["status"] = selected_status

# Input
claim_text = st.text_area("Patent Claim", height=150, placeholder="A method comprising a UE configured to...")

col1, col2 = st.columns([1, 4])
with col1:
    search_btn = st.button("Search", type="primary")

if search_btn and claim_text:
    with st.spinner("Processing Claim..."):
        # 1. Process Claim
        # Now returns (query, constraints)
        query, constraints = processor.process_claim(claim_text)
        
        st.subheader("Processed Query")
        st.info(query)
        
        if constraints:
            st.warning(f"Domain Constraints Applied: Must contain {constraints}")
        
        # 2. Search with Filters and Constraints
        results = searcher.search(query, top_k=10, filters=filters, must_have_terms=constraints)
        
        st.subheader(f"Top {len(results)} Results")
        
        if not results:
            st.warning("No results found matching the criteria.")
        else:
            for i, res in enumerate(results):
                chunk = res['chunk']
                score = res['score']
                metadata = chunk.get('metadata', {})
                
                with st.expander(f"{i+1}. [{metadata.get('type', 'DOC')}] {metadata.get('title', 'Untitled')} (Score: {score:.4f})"):
                    st.markdown(f"**Source:** {metadata.get('source', 'Unknown')} | **Status:** {metadata.get('status', 'Unknown')}")
                    st.markdown(f"**Relevance Score:** {score:.4f} (BM25: {res['bm25_score']:.4f}, Vector: {res['vector_score']:.4f})")
                    st.markdown("---")
                    st.markdown(chunk['text'])

elif search_btn:
    st.error("Please enter a claim.")
