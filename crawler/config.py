import os

# 3GPP FTP Server Configuration
FTP_HOST = "ftp.3gpp.org"
FTP_USER = "anonymous"
FTP_PASS = "anonymous"

# Local Download Configuration
# Default to a "data" directory in the project root
BASE_DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# Target Directories on FTP
# These are templates to be formatted with specific meeting/series details
TDOC_PATH_TEMPLATE = "/tsg_{wg}/WG{wg_num}_RL{wg_num}/TSG{wg}_{meeting}/Docs/"
REPORT_PATH_TEMPLATE = "/tsg_{wg}/WG{wg_num}_RL{wg_num}/TSG{wg}_{meeting}/Report/"
SPEC_SERIES_PATH_TEMPLATE = "/Specs/archive/{series}_series/"

# File Extensions to download
ALLOWED_EXTENSIONS = {".zip", ".doc", ".docx", ".pdf", ".txt"}

# GCS Configuration
GCS_BUCKET_NAME = "invention-platform-data-001"

