import zipfile
import os

def zip_project():
    output_filename = 'source.zip'
    # Folders to include
    include_folders = ['app', 'brain', 'crawler', 'refinery']
    # Files to include
    include_files = ['Dockerfile', 'requirements.txt', 'setup.py']
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add Root Files
        for file in include_files:
            if os.path.exists(file):
                print(f"Adding {file}...")
                zipf.write(file, file)
        
        # Add Folders
        for folder in include_folders:
            if not os.path.exists(folder):
                continue
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if '__pycache__' in root:
                        continue
                    if file.endswith('.pyc'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    print(f"Adding {file_path}...")
                    zipf.write(file_path, file_path)
    
    print(f"Created {output_filename}")

if __name__ == "__main__":
    zip_project()
