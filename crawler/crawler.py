import ftplib
import os
import time
from dataclasses import dataclass
from typing import List, Optional
from . import config

@dataclass
class Target:
    wg: str  # e.g., "ran"
    wg_num: str  # e.g., "1"
    meeting: str  # e.g., "104-e"
    type: str  # "Docs" or "Report"

class ThreeGPPCrawler:
    def __init__(self):
        self.ftp = None
        self.connected = False

    def connect(self):
        """Connects to the 3GPP FTP server."""
        try:
            print(f"Connecting to {config.FTP_HOST}...")
            self.ftp = ftplib.FTP(config.FTP_HOST)
            self.ftp.login(config.FTP_USER, config.FTP_PASS)
            self.connected = True
            print("Connected successfully.")
        except Exception as e:
            print(f"Error connecting to FTP: {e}")
            self.connected = False

    def disconnect(self):
        """Disconnects from the FTP server."""
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                self.ftp.close()
            self.connected = False
            print("Disconnected.")

    def _ensure_local_dir(self, path: str):
        """Creates the local directory if it doesn't exist."""
        if not os.path.exists(path):
            os.makedirs(path)

    def _is_file_downloaded(self, local_path: str, remote_size: int) -> bool:
        """Checks if the file is already downloaded and has the same size."""
        if os.path.exists(local_path):
            local_size = os.path.getsize(local_path)
            if local_size == remote_size:
                return True
        return False

    def download_directory(self, remote_dir: str, local_dir: str):
        """Recursively downloads a directory from FTP."""
        if not self.connected:
            self.connect()
            if not self.connected:
                return

        try:
            self.ftp.cwd(remote_dir)
            files = []
            self.ftp.dir(files.append)

            self._ensure_local_dir(local_dir)

            for line in files:
                parts = line.split()
                name = parts[-1]
                
                # Simple heuristic to distinguish files from directories
                # In unix FTP listing, first char 'd' means directory
                is_dir = line.startswith('d')
                
                if is_dir:
                    # Skip . and ..
                    if name in ['.', '..']:
                        continue
                    # Recursive call
                    new_remote = f"{remote_dir}/{name}"
                    new_local = os.path.join(local_dir, name)
                    self.download_directory(new_remote, new_local)
                else:
                    # It's a file
                    ext = os.path.splitext(name)[1].lower()
                    if ext in config.ALLOWED_EXTENSIONS:
                        remote_size = int(parts[4]) # Size is usually the 5th element
                        local_path = os.path.join(local_dir, name)
                        
                        if self._is_file_downloaded(local_path, remote_size):
                            print(f"Skipping {name} (already exists)")
                        else:
                            print(f"Downloading {name}...")
                            with open(local_path, 'wb') as f:
                                self.ftp.retrbinary(f"RETR {name}", f.write)
        except Exception as e:
            print(f"Error downloading from {remote_dir}: {e}")

    def crawl_target(self, target: Target):
        """Crawls a specific meeting target (Docs or Report)."""
        if target.type == "Docs":
            remote_path = config.TDOC_PATH_TEMPLATE.format(
                wg=target.wg, wg_num=target.wg_num, meeting=target.meeting
            )
        elif target.type == "Report":
            remote_path = config.REPORT_PATH_TEMPLATE.format(
                wg=target.wg, wg_num=target.wg_num, meeting=target.meeting
            )
        else:
            print(f"Unknown target type: {target.type}")
            return

        # Construct local path to mirror structure
        # data/tsg_ran/WG1_RL1/TSGR1_104-e/Docs/
        local_path = os.path.join(
            config.BASE_DOWNLOAD_DIR, 
            f"tsg_{target.wg}", 
            f"WG{target.wg_num}_RL{target.wg_num}", 
            f"TSG{target.wg}_{target.meeting}", 
            target.type
        )

        print(f"Starting crawl for {target.wg.upper()}{target.wg_num} #{target.meeting} ({target.type})")
        self.download_directory(remote_path, local_path)

    def crawl_specs(self, series: str):
        """Crawls specifications for a given series."""
        remote_path = config.SPEC_SERIES_PATH_TEMPLATE.format(series=series)
        local_path = os.path.join(config.BASE_DOWNLOAD_DIR, "Specs", "archive", f"{series}_series")
        
        print(f"Starting crawl for Specs Series {series}")
        self.download_directory(remote_path, local_path)

if __name__ == "__main__":
    crawler = ThreeGPPCrawler()
    
    # Example usage (commented out to avoid auto-run)
    # target = Target(wg="ran", wg_num="1", meeting="104-e", type="Docs")
    # crawler.crawl_target(target)
    
    crawler.disconnect()
