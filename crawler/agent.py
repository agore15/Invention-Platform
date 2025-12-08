import asyncio
import os
import sys
import re
import json
import requests
import zipfile
import io
import docx
from typing import Optional

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from crawler import config
from google.cloud import storage

class ThreeGPPCrawler:
    def __init__(self):
        self.storage_client = None
        self.bucket = None
        self.bucket_name = config.GCS_BUCKET_NAME
        try:
            self.storage_client = storage.Client(project=config.PROJECT_ID)
            self.bucket = self.storage_client.bucket(self.bucket_name)
            print(f'Initialized GCS bucket: {self.bucket_name} in project {config.PROJECT_ID}')
        except Exception as e:
            print(f'Warning: Failed to initialize GCS client: {e}')

    def download_directory(self, *args):
        # Adapter method for pipeline compatibility
        print('Starting Cloud Crawler...')
        asyncio.run(self.run())

    def upload_blob(self, source_data, destination_blob_name, content_type='application/octet-stream'):
        if not self.bucket:
            print('Skipping upload (No GCS Bucket)')
            return

        blob = self.bucket.blob(destination_blob_name)
        
        try:
            if isinstance(source_data, str):
                blob.upload_from_string(source_data, content_type=content_type)
            else:
                if hasattr(source_data, 'seek'):
                    source_data.seek(0)
                blob.upload_from_file(source_data, content_type=content_type)
            
            print(f'Uploaded to gs://{self.bucket_name}/{destination_blob_name}')
        except Exception as e:
            print(f'Failed to upload {destination_blob_name}: {e}')

    def blob_exists(self, blob_name):
        if not self.bucket: return False
        blob = self.bucket.blob(blob_name)
        return blob.exists()

    async def run(self):
        server_parameters = StdioServerParameters(
            command=sys.executable,
            args=['-m', 'mcp_3gpp_ftp.server'],
            env=os.environ.copy()
        )

        async with stdio_client(server_parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Full Target List
                specs_to_crawl = [
                    '38.211', '38.212', '38.213', '38.214',
                    '38.300', '38.321', '38.331', 
                    '38.401', '38.413', '38.901'
                ]
                
                base_ftp_path = '/Specs/archive/38_series'
                base_url = 'https://www.3gpp.org/ftp'
                
                for spec in specs_to_crawl:
                    spec_path = f'{base_ftp_path}/{spec}'
                    print(f'\nChecking {spec_path}...')
                    
                    try:
                        processed_blob_name = f'specs/processed/{spec}.txt'
                        if self.blob_exists(processed_blob_name):
                            print(f'Processed text for {spec} already in GCS. Skipping.')
                            continue

                        result = await session.call_tool('list_directories_files', arguments={'path': spec_path})
                        
                        filenames = []
                        for item in result.content:
                            if item.type == 'text':
                                filenames.append(item.text)
                        
                        relevant_files = [f for f in filenames if re.search(r'-(g|h)\d+\.zip$', f)]
                        
                        if not relevant_files:
                            print(f'No Rel-16/17 files found for {spec}')
                            continue
                            
                        latest_file = sorted(relevant_files)[-1]
                        # Fix: use spec name + version for stable naming if needed, but keeping original filename is fine
                        print(f'Found latest file: {latest_file}')
                        
                        full_url = f'{base_url}{spec_path}/{latest_file}'
                        
                        print(f'Downloading {full_url} (in-memory)...')
                        zip_buffer = io.BytesIO()
                        try:
                            with requests.get(full_url, stream=True, timeout=600) as r:
                                r.raise_for_status()
                                for chunk in r.iter_content(chunk_size=16384):
                                    zip_buffer.write(chunk)
                            print(f'Download complete ({zip_buffer.tell()} bytes).')
                        except Exception as e:
                            print(f'Download failed for {spec}: {e}')
                            continue
                            
                        # Upload Raw ZIP
                        raw_zip_blob = f'specs/raw/{latest_file}'
                        self.upload_blob(zip_buffer, raw_zip_blob, 'application/zip')
                        
                        # Process
                        try:
                            with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                                extracted_files = zip_ref.namelist()
                                doc_file = next((f for f in extracted_files if f.endswith('.docx')), None)
                                
                                if doc_file:
                                    print(f'Processing {doc_file}...')
                                    with zip_ref.open(doc_file) as doc_stream:
                                        doc_buffer = io.BytesIO(doc_stream.read())
                                        
                                        # Upload Raw DOCX
                                        raw_doc_blob = f'specs/raw/{doc_file}'
                                        self.upload_blob(doc_buffer, raw_doc_blob, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                                        
                                        # Parse
                                        doc = docx.Document(doc_buffer)
                                        full_text = []
                                        for para in doc.paragraphs:
                                            full_text.append(para.text)
                                        
                                        # Use proper newline
                                        content_text = '\n'.join(full_text)
                                        
                                        self.upload_blob(content_text, processed_blob_name, 'text/plain')
                                        print(f'Successfully processed {spec}')
                                else:
                                    print('No .docx found in zip.')
                        except Exception as e:
                            print(f'Extraction/Processing failed: {e}')
                            
                    except Exception as e:
                        print(f'Error crawling {spec}: {e}')

                print('Cloud Crawler run complete.')

if __name__ == '__main__':
    agent = ThreeGPPCrawler()
    asyncio.run(agent.run())
