import sys
import os
import subprocess
from pathlib import Path

def open_utlink(utlink_path_str):
    """Reads a .utlink file, finds the real file, and opens it natively."""
    utlink_path = Path(utlink_path_str).resolve()
    
    if not utlink_path.exists() or utlink_path.suffix != '.utlink':
        print(f"Error: '{utlink_path_str}' is not a valid .utlink file.")
        return

    try:
        with open(utlink_path, 'r', encoding='utf-8') as f:
            target_rel_path = f.read().strip()
    except Exception as e:
        print(f"Error reading .utlink file: {e}")
        return

    # Dynamically find the User Root directory by scanning upward
    real_file = None
    current_dir = utlink_path.parent
    
    while current_dir != current_dir.parent: # Stop if we hit the root of the drive
        potential_user_root = current_dir.parent
        potential_real_file = potential_user_root / target_rel_path
        
        if potential_real_file.exists():
            real_file = potential_real_file
            break
            
        current_dir = current_dir.parent

    if not real_file:
        print(f"Error: Could not locate the original physical file.")
        print(f"Expected to find it via: {target_rel_path}")
        return

    print(f"Opening physical file: {real_file}")
    
    # Trigger the OS to open the real file using its default terminal or GUI app
    try:
        if sys.platform == "darwin":           # macOS
            subprocess.run(['open', str(real_file)])
        elif sys.platform.startswith("linux"): # Linux
            subprocess.run(['xdg-open', str(real_file)])
        elif sys.platform == "win32":          # Windows
            os.startfile(str(real_file))
    except Exception as e:
        print(f"Failed to open file: {e}")

if __name__ == "__main__":
    # Check if a file path was passed in the terminal
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.endswith('.utlink'):
            open_utlink(arg)
        else:
            print(f"Error: '{arg}' is not a .utlink file.")
            print("Usage: python3 utlink_open.py /path/to/file.utlink")
    else:
        print("UniversalTransfer Link Opener")
        print("Usage: python3 utlink_open.py /path/to/file.utlink")