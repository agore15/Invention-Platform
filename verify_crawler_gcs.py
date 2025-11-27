from crawler.crawler import ThreeGPPCrawler
from crawler import config
import os
import time

class TestCrawler(ThreeGPPCrawler):
    def download_directory(self, remote_dir: str, local_dir: str):
        """Override to only download files in the top level, no recursion."""
        if not self.connected:
            self.connect()
            if not self.connected:
                return

        try:
            print(f"Listing {remote_dir}...")
            self.ftp.cwd(remote_dir)
            files = []
            self.ftp.dir(files.append)

            self._ensure_local_dir(local_dir)

            for line in files:
                parts = line.split()
                name = parts[-1]
                is_dir = line.startswith("d")
                
                if is_dir:
                    print(f"Skipping directory: {name}")
                    continue
                
                # It is a file
                ext = os.path.splitext(name)[1].lower()
                if ext in config.ALLOWED_EXTENSIONS:
                    print(f"Found candidate file: {name}")
                    remote_size = int(parts[4])
                    local_path = os.path.join(local_dir, name)
                    
                    print(f"Downloading {name}...")
                    with open(local_path, "wb") as f:
                        self.ftp.retrbinary(f"RETR {name}", f.write)
                    
                    # This triggers the upload
                    self.upload_to_gcs(local_path, remote_dir)
                    
                    # Stop after one file for testing
                    print("Test: Stopped after one file.")
                    return

        except Exception as e:
            print(f"Error in test download: {e}")

def verify_gcs_upload():
    print("Starting Crawler GCS Verification...")
    crawler = TestCrawler()
    
    # Target a directory known to have a file
    # /tsg_ran/WG1_RL1/TSGR1_104-e/Report/ has "Final_Minutes_report_RAN1#104-e_v100.zip"
    target_remote = "/tsg_ran/WG1_RL1/TSGR1_104-e/Report/"
    target_local = os.path.join(config.BASE_DOWNLOAD_DIR, "test_verification")
    
    # Clean up local if exists
    if os.path.exists(target_local):
        import shutil
        shutil.rmtree(target_local)

    crawler.download_directory(target_remote, target_local)
    crawler.disconnect()
    
    print("\nVerification complete. Check GCS bucket for uploaded file.")

if __name__ == "__main__":
    verify_gcs_upload()

