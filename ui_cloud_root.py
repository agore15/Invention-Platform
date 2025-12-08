import streamlit as st
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath('.'))

from app.claim_processor import ClaimProcessor
from brain.search_cloud import CloudSearcher

# Initialize components (cache to avoid reloading on every interaction)
@st.cache_resource
def load_components():
    processor = ClaimProcessor()
    # Use the new CloudSearcher
    searcher = CloudSearcher()
    return processor, searcher

processor, searcher = load_components()

st.set_page_config(page_title='3GPP Claim-to-Search (Cloud)', layout='wide')

st.title('3GPP Claim-to-Search (Cloud Native)')
st.caption('Powered by Google Vertex AI & Firestore')
st.markdown('Enter a patent claim below to find relevant 3GPP TDocs.')

# Sidebar Filters
st.sidebar.header('Filters')

# 1. Document Type Filter
available_types = searcher.get_unique_metadata_values('type')
default_types = [t for t in available_types if t != 'LS']
if not default_types and available_types:
    default_types = available_types

selected_types = st.sidebar.multiselect(
    'Document Type',
    options=available_types,
    default=default_types,
    help='Select document types to include.'
)

# 2. Source Filter
available_sources = searcher.get_unique_metadata_values('source')
selected_source = st.sidebar.selectbox(
    'Source',
    options=['All'] + available_sources,
    help='Filter by source organization.'
)

# 3. Status Filter
available_statuses = searcher.get_unique_metadata_values('status')
selected_status = st.sidebar.selectbox(
    'Status',
    options=['All'] + available_statuses,
    help='Filter by document status.'
)

# Construct Filters Dictionary
filters = {}
if selected_types:
    filters['type'] = selected_types

if selected_source != 'All':
    filters['source'] = selected_source

if selected_status != 'All':
    filters['status'] = selected_status

# Input
claim_text = st.text_area('Patent Claim', height=150, placeholder='A method comprising a UE configured to...')

col1, col2 = st.columns([1, 4])
with col1:
    search_btn = st.button('Search', type='primary')

if search_btn and claim_text:
    with st.spinner('Processing Claim & Searching Vertex AI...'):
        # 1. Process Claim
        query, constraints = processor.process_claim(claim_text)
        
        st.subheader('Processed Query')
        st.info(query)
        
        if constraints:
            st.warning(f'Domain Constraints Applied: Must contain {constraints}')
        
        # 2. Search
        results = searcher.search(query, top_k=10, filters=filters, must_have_terms=constraints)
        
        st.subheader(f'Top {len(results)} Results')
        
        if not results:
            st.warning('No results found matching the criteria.')
        else:
            for i, res in enumerate(results):
                doc_text = res.get('text', '')
                score = res.get('score', 0.0)
                metadata = res.get('metadata', {})
                bm25 = res.get('bm25_score', 0)
                vec_sc = res.get('vector_score', 0)
                
                with st.expander(f'{i+1}. [{metadata.get('type', 'DOC')}] {metadata.get('source', '3GPP Spec')} (Score: {score:.4f})'):
                    st.markdown(f'**URI:** {metadata.get('gcs_uri', 'N/A')}')
                    st.markdown(f'**Relevance Score:** {score:.4f} (Vector: {vec_sc:.4f})')
                    st.markdown('---')
                    st.markdown(doc_text)

elif search_btn:
    st.error('Please enter a claim.')
