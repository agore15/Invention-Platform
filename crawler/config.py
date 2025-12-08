import os

# 3GPP FTP Server Configuration
FTP_HOST = 'ftp.3gpp.org'
FTP_USER = 'anonymous'
FTP_PASS = 'anonymous'

# Local Download Configuration
BASE_DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# Target Directories on FTP
TDOC_PATH_TEMPLATE = '/tsg_{wg}/WG{wg_num}_RL{wg_num}/TSG{wg}_{meeting}/Docs/'
REPORT_PATH_TEMPLATE = '/tsg_{wg}/WG{wg_num}_RL{wg_num}/TSG{wg}_{meeting}/Report/'
SPEC_SERIES_PATH_TEMPLATE = '/Specs/archive/{series}_series/'

# File Extensions to download
ALLOWED_EXTENSIONS = {'.zip', '.doc', '.docx', '.pdf', '.txt'}

# GCS Configuration
GCS_BUCKET_NAME = 'invention-platform-data-001'
PROJECT_ID = 'still-manifest-478014-c1'
REGION = 'us-central1'

# Vertex AI Configuration
VECTOR_INDEX_DISPLAY_NAME = '3gpp-knowledge-base-index'
VECTOR_INDEX_ENDPOINT_DISPLAY_NAME = '3gpp-knowledge-base-endpoint'
VECTOR_INDEX_ENDPOINT_ID = 'projects/941721845440/locations/us-central1/indexEndpoints/2589132180110180352'
