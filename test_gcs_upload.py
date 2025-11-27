from crawler.crawler import ThreeGPPCrawler
from crawler import config
import os

def test_upload():
    print("Testing GCS Upload...")
    crawler = ThreeGPPCrawler()
    if not crawler.bucket:
        print("FAIL: Bucket not initialized")
        return

    # Ensure data dir exists
    if not os.path.exists(config.BASE_DOWNLOAD_DIR):
        os.makedirs(config.BASE_DOWNLOAD_DIR)

    # Create a dummy file in data dir
    test_file = os.path.join(config.BASE_DOWNLOAD_DIR, "test_upload.txt")
    with open(test_file, "w") as f:
        f.write("This is a test file for GCS upload.")

    try:
        # Upload it
        crawler.upload_to_gcs(test_file, "/unused/remote/path")
        print("PASS: Upload logic executed")
    except Exception as e:
        print(f"FAIL: Upload failed: {e}")
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_upload()

