# Security & Privacy Architecture

## 1. Zero-Retention & Data Sovereignty

To ensure that proprietary inputs (Patent Claims) never become part of a public model's training set:

- **Zero-Retention Policy**: The LLM provider (Vertex AI) must be configured with "Enterprise Privacy" settings.
- **Requirement**: Inputs (Claims) and outputs (Answers) must not be logged, stored, cached, or used for model training/tuning by the provider at any time.
- **Data Residency**: All data processing and storage (GCS, Vector DB, Compute) must be restricted to a specific geographic region (e.g., `us-central1` or `europe-west4`) to comply with corporate data governance policies.

## 2. Network Security (VPC Controls)

To prevent accidental exposure of proprietary data to the public internet:

- **VPC Service Controls**: All data traffic between the Application, Vector Database, and LLM API must remain within a Virtual Private Cloud (VPC) perimeter.
- **Private Connectivity**:
    - The connection between the application container (Cloud Run) and the Vector Database must use private IP addresses.
    - Egress to the 3GPP FTP server (public internet) must be strictly allow-listed via a Cloud NAT gateway.

## 3. Application-Level Privacy Controls

- **"Privacy-Preserving RAG" (Sanitized Mode)**:
    - **Feature**: The UI includes a toggle for "Sanitized Mode" (Default: ON).
    - **Behavior**:
        - **Local Tokenization**: The application locally extracts technical keywords and acronyms.
        - **Payload Replacement**: The system discards the original natural language claim.
        - **Sanitized Request**: The system sends only the list of technical tokens + the retrieved 3GPP text chunks to the LLM.
    - **Local Processing Guarantee**: The "Claim-to-Search" translation logic runs entirely on internal compute resources.

## 4. Access Control (IAM)

- **Identity Awareness**: The application must be fronted by Identity-Aware Proxy (IAP).
- **Role-Based Access**: Only authorized "Legal/IP Team" members may access the search interface. Developers should have access only to the infrastructure code.
