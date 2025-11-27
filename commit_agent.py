import subprocess
import time
import datetime
import os

# Configuration
DEBOUNCE_SECONDS = 300  # 5 minutes of inactivity required
CHECK_INTERVAL_SECONDS = 10 # Check for changes every 10 seconds

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # git status returns non-zero if not a git repo, etc.
        # But here we expect it to work if we are in a repo.
        print(f"Error running command {' '.join(command)}: {e}")
        return None

def get_git_status():
    """Returns the output of git status --porcelain."""
    return run_command(['git', 'status', '--porcelain'])

def get_modified_files(status_output):
    """Parses git status output to get a list of modified/untracked files."""
    if not status_output:
        return []
    
    files = []
    for line in status_output.splitlines():
        # Format is "XY filename" or "XY  filename"
        # Porcelain v1: 2 chars status, 1 space, filename.
        # If filename has spaces, it might be quoted? git status --porcelain usually handles this.
        # Simple split might be risky for filenames with spaces, but let's try basic parsing.
        # Ideally we use -z but that returns null-terminated strings, harder to read in simple python script without more logic.
        # For this agent, we'll assume standard filenames or simple parsing.
        parts = line.strip().split(' ', 1)
        if len(parts) == 2:
            files.append(parts[1].strip())
    return files

def get_last_modified_time(files):
    """Returns the latest modification time among the given files."""
    last_mtime = 0
    for file in files:
        # Handle paths with spaces or quotes if git output them
        clean_path = file.strip('"') 
        if os.path.exists(clean_path):
            mtime = os.path.getmtime(clean_path)
            if mtime > last_mtime:
                last_mtime = mtime
    return last_mtime

def git_add():
    """Stages all changes."""
    print("Staging changes...")
    run_command(['git', 'add', '.'])

def git_commit(message):
    """Commits changes with a message."""
    print(f"Committing with message: {message}")
    run_command(['git', 'commit', '-m', message])

def git_push():
    """Pushes changes to remote."""
    print("Pushing changes...")
    run_command(['git', 'push'])

def main():
    print(f"Starting Commit Agent with Debounce Logic.")
    print(f"Debounce Time: {DEBOUNCE_SECONDS} seconds.")
    print("Press Ctrl+C to stop.")
    
    # State
    pending_changes = False
    
    try:
        while True:
            status = get_git_status()
            
            if status:
                files = get_modified_files(status)
                last_mtime = get_last_modified_time(files)
                current_time = time.time()
                time_since_last_edit = current_time - last_mtime
                
                if not pending_changes:
                    print(f"[{datetime.datetime.now()}] Changes detected. Waiting for inactivity...")
                    pending_changes = True
                
                # Check if enough time has passed since the last file edit
                if time_since_last_edit > DEBOUNCE_SECONDS:
                    print(f"[{datetime.datetime.now()}] No activity for {int(time_since_last_edit)}s. Committing.")
                    
                    git_add()
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    git_commit(f"Auto-commit: {timestamp}")
                    git_push()
                    
                    pending_changes = False
                else:
                    # Still active or waiting
                    # Optional: Print countdown or status?
                    # print(f"Waiting... ({int(time_since_last_edit)}s since last edit)")
                    pass
            else:
                if pending_changes:
                    # Changes disappeared (e.g. reverted manually)?
                    print("Changes no longer detected.")
                    pending_changes = False
            
            time.sleep(CHECK_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\nStopping Commit Agent.")

if __name__ == "__main__":
    main()
