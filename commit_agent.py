import subprocess
import os

def get_git_status():
    """Returns the output of git status --porcelain."""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_changes_stat():
    """Returns the output of git diff --shortstat."""
    try:
        # Check staged changes
        result = subprocess.run(['git', 'diff', '--cached', '--shortstat'], capture_output=True, text=True)
        staged = result.stdout.strip()
        
        # Check unstaged changes
        result = subprocess.run(['git', 'diff', '--shortstat'], capture_output=True, text=True)
        unstaged = result.stdout.strip()
        
        return staged, unstaged
    except subprocess.CalledProcessError:
        return None, None

def should_commit():
    """Decides if a commit should be made based on heuristics."""
    status = get_git_status()
    
    if not status:
        print("No changes detected or not a git repository.")
        return False

    print(f"Detected changes:\n{status}")
    
    staged, unstaged = get_changes_stat()
    print(f"Staged stats: {staged}")
    print(f"Unstaged stats: {unstaged}")

    # Heuristic 1: If there are staged changes, we should probably commit (or amend).
    if staged:
        print("DECISION: COMMIT (Staged changes present)")
        return True

    # Heuristic 2: If there are many unstaged changes, maybe we should stage and commit.
    # Simple line count parsing could go here, but for now, existence is enough to suggest action.
    if unstaged:
        print("DECISION: SUGGEST STAGE & COMMIT (Unstaged changes present)")
        return True
        
    # Heuristic 3: Untracked files (?? in status)
    if "??" in status:
        print("DECISION: SUGGEST ADD & COMMIT (Untracked files present)")
        return True

    return False

if __name__ == "__main__":
    should_commit()
