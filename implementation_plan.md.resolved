# Implementation Plan - Phase 1: 3GPP FTP Crawler

## Goal
Build a lightweight, robust crawler to mirror specific 3GPP documents (TDocs, Meeting Reports, Specifications) from `ftp.3gpp.org` to a local directory (simulating Cloud Storage for this phase). This data will later be used to build a claim chart against private user inventions.

## User Review Required
> [!IMPORTANT]
> **Privacy & Data Flow**: The crawler only fetches **public** data from 3GPP. No private user data (claims/inventions) is involved in the crawling process. The matching/search (Phase 3 & 4) will happen entirely within your secure environment using this downloaded data.

## Proposed Changes

### [Crawler Module]
We will create a new Python module `crawler` with the following structure:

#### [NEW] [crawler.py](file:///C:/Users/aaron/.gemini/antigravity/brain/2a86ebd5-78a4-493c-80df-6842366fd007/crawler/crawler.py)
-   Main entry point.
-   Handles FTP connection and navigation.
-   Implements "Delta Sync" (checking file timestamps/sizes before downloading).
-   **Key Classes**:
    -   `ThreeGPPCrawler`: Main class to manage the FTP session.
    -   `Target`: Data class to define what to crawl (e.g., "RAN1", "Meeting 104", "TDocs").

#### [NEW] [config.py](file:///C:/Users/aaron/.gemini/antigravity/brain/2a86ebd5-78a4-493c-80df-6842366fd007/crawler/config.py)
-   Configuration for FTP URL, target directories, and local download paths.

### Targets
Based on initial exploration, the crawler will target:
1.  **TDocs (Contributions)**: `ftp/tsg_{wg}/WG{n}_RL{n}/TSG{wg}_{meeting}/Docs/`
2.  **Meeting Reports**: `ftp/tsg_{wg}/WG{n}_RL{n}/TSG{wg}_{meeting}/Report/`
3.  **Specifications (TS)**: `ftp/Specs/archive/{series}_series/` (and potentially latest versions in `ftp/Specs/`)

## Verification Plan

### Automated Tests
-   Unit tests for the `Delta Sync` logic (mocking FTP responses).
-   Integration test: Connect to 3GPP FTP and list files in a known directory (e.g., a specific meeting folder) without downloading everything.

### Manual Verification
-   Run the crawler for a **single specific meeting** (e.g., RAN1#104-e) to verify it correctly downloads:
    -   TDocs (.zip/.doc)
    -   Report (.zip/.doc)
-   Verify folder structure is preserved locally.
