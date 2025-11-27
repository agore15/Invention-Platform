# SOW Review: 3GPP AI Prior Art Search Engine

## Executive Summary
The SOW describes a clear and high-value project: building a specialized RAG (Retrieval-Augmented Generation) system for 3GPP telecommunications standards. The architecture follows a standard and robust pattern for this type of application: **Ingest -> Process -> Index -> Serve**.

The timeline (8-10 weeks) is ambitious, particularly regarding the "Refinery" phase (parsing complex Word documents with track changes), which is correctly identified as the most critical technical challenge.

## Strengths
-   **Clear Architecture**: The separation into Crawler, Refinery, Brain, and Application phases is logical and follows best practices.
-   **Specific Requirements**: The SOW clearly identifies key challenges like "Delta Sync" for the crawler and "Track Changes" handling for the parser.
-   **Tech Stack**: The choice of GCP (Vertex AI, GCS, Cloud Run) is well-suited for a scalable, cloud-native AI application.
-   **Hybrid Search**: Explicitly requiring both Semantic and Keyword (BM25) search is excellent. Pure vector search often fails on specific technical identifiers (like "SCS 30kHz"), so this hybrid approach is crucial for technical domains.

## Risks & Challenges
### 1. The "Refinery" (Data Parsing) - **High Risk**
-   **Complexity**: Parsing `.doc` and `.docx` files programmatically while respecting "Track Changes" is non-trivial. Libraries like `python-docx` handle `.docx` well but may struggle with complex revision histories or older `.doc` binary formats.
-   **Recommendation**: We may need to use tools like `pandoc` or even headless LibreOffice for robust conversion if Python libraries fall short. We should prototype this immediately.

### 2. Data Volume & Crawler Politeness
-   **Risk**: Mirroring the 3GPP FTP server can involve massive amounts of data.
-   **Recommendation**: Ensure the crawler respects `robots.txt` (if applicable) or implements rate limiting to avoid getting banned. The "Delta Sync" requirement is essential here.

### 3. Vector Database Costs & Scale
-   **Risk**: Vertex AI Vector Search is powerful but can have a higher minimum cost/complexity than lightweight alternatives.
-   **Recommendation**: For the initial MVP, using a managed Pinecone instance or even a Postgres `pgvector` instance (on Cloud SQL) might be more cost-effective and easier to set up, unless the dataset is massive (millions of vectors).

## Technical Recommendations
1.  **Parser Prototype**: Prioritize building a proof-of-concept for the "Track Changes" parser in Week 1. If this fails, the entire pipeline is blocked.
2.  **Infrastructure as Code (IaC)**: Use Terraform or Pulumi to define the GCP infrastructure. This ensures the environment is reproducible.
3.  **Evaluation Framework**: Define a "Golden Set" of questions and answers early on to programmatically measure the RAG system's accuracy (using metrics like RAGAS).

## Clarification Questions
1.  **Authentication**: Who are the users? Do we need to integrate with an internal SSO (Single Sign-On) provider, or is a simple email/password (Firebase Auth) sufficient?
2.  **Legacy Formats**: How far back does the archive go? Are we dealing with very old Word 97 files?
3.  **Budget**: Is there a specific cloud budget cap for the development phase?
