import streamlit as st
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application.query_processor import QueryProcessor
from application.search import SearchEngine

def main():
    st.set_page_config(page_title="Invention Platform", layout="wide")
    st.title("Invention Platform - RAG Interface")

    # Sidebar
    st.sidebar.header("Filters")
    sanitized_mode = st.sidebar.toggle("Sanitized Mode", value=True)
    status_filter = st.sidebar.multiselect("Status", ["Agreed", "Not Agreed", "Draft"])
    source_filter = st.sidebar.text_input("Source (e.g., Qualcomm)")

    # Main Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Describe your invention..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process Query
        processor = QueryProcessor()
        
        if sanitized_mode:
            processed_query = processor.sanitize(prompt)
            st.info(f"Sanitized Query Tokens: {processed_query}")
        else:
            processed_query = processor.process(prompt)
            st.info(f"Processed Query: {processed_query}")
        
        with st.chat_message("assistant"):
            
            # Search
            engine = SearchEngine()
            results = engine.search(str(processed_query), filters={"status": status_filter, "source": source_filter})
            
            response = engine.generate_answer(results, processed_query)
            st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
