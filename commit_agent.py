import subprocess
import time
import datetime

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e}")
        return None

def get_git_status():
    """Returns the output of git status --porcelain."""
    return run_command(['git', 'status', '--porcelain'])

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

def check_and_commit():
    """Checks for changes and commits them if found."""
    status = get_git_status()
    
    if not status:
        # No changes
        return

    print(f"[{datetime.datetime.now()}] Changes detected:\n{status}")
    
    # Heuristic: If there are any changes (staged, unstaged, or untracked), we commit.
    git_add()
    
    # Generate a simple commit message with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Auto-commit: {timestamp}"
    
    git_commit(commit_message)
    git_push()

def main():
    print("Starting Commit Agent in automatic mode...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            check_and_commit()
            time.sleep(60) # Check every 60 seconds
    except KeyboardInterrupt:
        print("\nStopping Commit Agent.")

if __name__ == "__main__":
    main()
