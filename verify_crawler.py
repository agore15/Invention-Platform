from crawler.crawler import ThreeGPPCrawler, Target

def test_connection():
    print("Testing FTP Connection...")
    crawler = ThreeGPPCrawler()
    crawler.connect()
    if crawler.connected:
        print("PASS: Connection successful")
    else:
        print("FAIL: Connection failed")
    crawler.disconnect()

def test_crawl_small_target():
    print("\nTesting Crawl (Dry Run / Listing)...")
    # We'll try to list a known directory without downloading everything to save time/bandwidth
    # Using a specific meeting folder that should exist
    crawler = ThreeGPPCrawler()
    crawler.connect()
    
    if crawler.connected:
        # Manually list a directory to verify navigation
        try:
            target_dir = "/tsg_ran/WG1_RL1/TSGR1_104-e/Report/"
            print(f"Listing contents of {target_dir}...")
            files = []
            crawler.ftp.cwd(target_dir)
            crawler.ftp.dir(files.append)
            
            if len(files) > 0:
                print(f"PASS: Successfully listed {len(files)} items.")
                print("First 3 items:")
                for f in files[:3]:
                    print(f)
            else:
                print("WARN: Directory is empty or listing failed.")
        except Exception as e:
            print(f"FAIL: Error listing directory: {e}")
        
        crawler.disconnect()

if __name__ == "__main__":
    test_connection()
    test_crawl_small_target()
