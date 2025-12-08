# Implementation Plan: 3GPP AI Prior Art Search Engine (SOW v2)

## Goal
Build a "Claim-to-Search" engine that ingests 3GPP documents, understands technical vocabulary, and retrieves evidence to validate Standard Essential Patents (SEPs).

## User Review Required
> [!IMPORTANT]
> **Refinery Complexity:** Parsing "Reason for Change" from Word tables and handling "Track Changes" are high-risk tasks requiring significant testing.
> **Claim-to-Search Logic:** The quality of retrieval depends heavily on the accuracy of the "Legalese Stripper" and "Acronym Injection" modules.

## Proposed Changes

### Phase 1: Data Ingestion (Crawler) - *Completed*
- [x] Crawler for TDocs and Reports
- [x] GCS Integration (`invention-platform-data-001`)

### Phase 2: The Refinery (Parsing & Cleaning)
#### [NEW] `refinery/vocabulary.py`
- Ingest TR 21.905 (Vocabulary) to build a Python dictionary of acronyms.
- Output: `acronyms.json`

#### [NEW] `refinery/parser.py`
- Implement `python-docx` logic to parse Word documents.
- **Track Changes:** Logic to "accept all changes" (or extract final text).
- **CR Extraction:** specialized logic to find and extract "Reason for Change" and "Summary of Change" tables from Change Requests.
- **Metadata:** Extract TDoc #, Source, Date, Meeting ID.

### Phase 3: The Brain (Vectorization)
#### [NEW] `brain/indexer.py`
- **Chunking:** Semantic chunking (by paragraph/section).
- **Embedding:** Use Vertex AI `text-embedding-004`.
- **Indexing:** Store in Vertex AI Vector Search (or Pinecone for MVP).
- **Hybrid Search:** Implement BM25 + Vector Search.

### Phase 4: The Application (Claim-to-Search UI)
#### [NEW] `app/claim_processor.py`
- **Legalese Stripper:** Use `spaCy` to remove patent stop-words ("comprising", "plurality of").
- **Acronym Injection:** Expand terms using `acronyms.json` (e.g., "UE" -> "User Equipment").

#### [NEW] `app/ui.py`
- Streamlit interface for users to input claims.
- Display retrieved TDocs with "Reason for Change" highlighted.

### Phase 5: Deployment
#### [NEW] Dockerfile
- Docker configuration for the Streamlit app.
- Base image: python:3.11-slim

#### [NEW] Cloud Run
- Deploy the containerized application to Google Cloud Run.
- Ensure access to Vertex AI and Firestore via Service Account.

## Verification Plan

### Automated Tests
- **Parser Tests:** Unit tests for `refinery/parser.py` using sample CRs with known "Reason for Change" content.
- **Vocabulary Tests:** Verify that common acronyms (UE, gNB) are correctly extracted from TR 21.905.
- **Search Tests:** "Golden Set" evaluation—input a known patent claim and verify the correct TDoc is in the top 10 results.

### Manual Verification
- Review parsed JSON output for complex CRs to ensure table structure is preserved.
- Test the UI with real patent claims to validate the "Claim-to-Search" translation.
