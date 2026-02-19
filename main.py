import os
import sys
import shutil
import platform
import getpass
from datetime import datetime
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    print("Error: The 'tqdm' library is required for progress bars.")
    print("Please install it by running: pip install tqdm")
    sys.exit(1)

CATEGORIES = ['Documents', 'Pictures', 'Videos', 'Music', 'Desktop', 'Downloads']

# Ignore hidden files/folders and specific system clutter
IGNORE_NAMES = {'thumbs.db', 'desktop.ini'}

def is_ignored(name):
    """Returns True if a file or folder is hidden or in the ignore list."""
    return name.startswith('.') or name.lower() in IGNORE_NAMES

def get_os_paths():
    """Maps standard folder categories to their OS-specific paths."""
    home = Path.home()
    paths = {}
    system = platform.system()
    
    for cat in CATEGORIES:
        if cat == 'Videos' and system == 'Darwin':
            paths[cat] = home / 'Movies'
        else:
            paths[cat] = home / cat
            
    return paths

def count_files(directory, recursive=True):
    """Counts total files, respecting ignore rules and depth."""
    count = 0
    for root, dirs, files in os.walk(directory):
        if not recursive:
            dirs[:] = [] 
        else:
            dirs[:] = [d for d in dirs if not is_ignored(d)]
            
        files = [f for f in files if not is_ignored(f)]
        count += len(files)
    return count

def get_dir_size(directory, recursive=True):
    """Calculates total size, respecting ignore rules and depth."""
    total_size = 0
    try:
        for root, dirs, files in os.walk(directory):
            if not recursive:
                dirs[:] = []
            else:
                dirs[:] = [d for d in dirs if not is_ignored(d)]
                
            for f in files:
                if is_ignored(f):
                    continue
                fp = Path(root) / f
                if fp.is_file() and not fp.is_symlink():
                    try:
                        total_size += fp.stat().st_size
                    except OSError:
                        pass
    except OSError:
        pass
    return total_size

def format_size(size_in_bytes):
    """Converts bytes to a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"

def copy_with_progress(src_dir, dst_dir, desc="Copying", rename_on_collision=False, recursive=True):
    """Copies files, skipping ignored files and respecting directory depth."""
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    
    if not src_dir.exists():
        return
        
    total_files = count_files(src_dir, recursive)
    if total_files == 0:
        return

    with tqdm(total_files=total_files, desc=desc, unit="file", leave=True) as pbar:
        for root, dirs, files in os.walk(src_dir):
            if not recursive:
                dirs[:] = []
            else:
                dirs[:] = [d for d in dirs if not is_ignored(d)]
            
            rel_path = Path(root).relative_to(src_dir)
            target_dir = dst_dir / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for file in files:
                if is_ignored(file):
                    continue 
                    
                src_file = Path(root) / file
                
                if not src_file.is_file() or src_file.is_symlink():
                    continue

                dst_file = target_dir / file
                
                try:
                    if rename_on_collision:
                        current_check = dst_file
                        counter = 1
                        already_restored = False
                        
                        while current_check.exists():
                            if os.path.getsize(src_file) == os.path.getsize(current_check) and \
                               os.path.getmtime(src_file) == os.path.getmtime(current_check):
                                already_restored = True
                                break
                            
                            current_check = target_dir / f"{dst_file.stem}_{counter}{dst_file.suffix}"
                            counter += 1
                            
                        if already_restored:
                            pbar.update(1)
                            continue 
                            
                        dst_file = current_check
                        shutil.copy2(src_file, dst_file)
                        
                    else:
                        if not dst_file.exists() or os.path.getmtime(src_file) > os.path.getmtime(dst_file):
                            shutil.copy2(src_file, dst_file)
                            
                except PermissionError:
                    tqdm.write(f"Permission denied: Skipping {src_file}")
                except Exception as e:
                    tqdm.write(f"Error copying {src_file}: {e}")
                    
                pbar.update(1)

def backup(dest_input):
    """Backs up user folders and loose files into a username-specific directory."""
    username = getpass.getuser()
    dest_base = Path(dest_input) / username
    dest_base.mkdir(parents=True, exist_ok=True)
    
    print(f"\nCalculating backup size for user '{username}'...")
    total_backup_size = 0
    folder_sizes = {} 
    
    paths = get_os_paths()
    for cat, src_path in paths.items():
        if src_path.exists():
            size = get_dir_size(src_path, recursive=True)
            folder_sizes[cat] = size
            total_backup_size += size
            
    home_path = Path.home()
    user_loose_size = get_dir_size(home_path, recursive=False)
    folder_sizes['user'] = user_loose_size
    total_backup_size += user_loose_size
            
    _, _, free_space = shutil.disk_usage(dest_base)
    
    print(f"Total backup size: {format_size(total_backup_size)}")
    print(f"Available space:   {format_size(free_space)}")
    
    if total_backup_size > free_space:
        print("\nError: Not enough free space on the destination drive.")
        print("Backup aborted.")
        return
        
    print("\nSpace check passed. Starting backup...")
    
    current_time = datetime.now()
    timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = current_time.strftime("%Y%m%d_%H%M%S")
    report_path = dest_base / f"backup_report_{file_timestamp}.txt"
    
    # Grab detailed system information
    system_name = platform.node()
    os_type = f"{platform.system()} {platform.release()}"
    
    with open(report_path, "w") as report:
        report.write("=== CROSS-PLATFORM BACKUP REPORT ===\n")
        report.write(f"Date/Time   : {timestamp_str}\n")
        report.write(f"User        : {username}\n")
        report.write(f"System Name : {system_name}\n")
        report.write(f"Source OS   : {os_type}\n")
        report.write(f"Target Dir  : {dest_base}\n")
        report.write("-" * 50 + "\n")
        report.write(f"{'Category':<15} | {'Size':<12} | {'Status'}\n")
        report.write("-" * 50 + "\n")
        
        # Backup standard folders
        for cat, src_path in paths.items():
            if src_path.exists():
                size = folder_sizes[cat]
                copy_with_progress(src_path, dest_base / cat, desc=f"Backing up {cat:<10}", recursive=True)
                report.write(f"{cat:<15} | {format_size(size):<12} | Successfully backed up\n")
            else:
                report.write(f"{cat:<15} | {'0.00 B':<12} | Skipped (Folder not found)\n")
                
        if user_loose_size > 0:
            copy_with_progress(home_path, dest_base / 'user', desc=f"Backing up {'user':<10}", recursive=False)
            report.write(f"{'user (loose)':<15} | {format_size(user_loose_size):<12} | Successfully backed up\n")
            
        report.write("-" * 50 + "\n")
        report.write(f"Total Backup Size Processed: {format_size(total_backup_size)}\n")
        report.write("-" * 50 + "\n")
        
        # This line is ONLY written if the script successfully finishes everything
        report.write("[BACKUP COMPLETED SUCCESSFULLY]\n")
        
    print(f"\nBackup complete! Report saved to: {report_path}")

def restore(src_input):
    """Scans for completed backups and restores files from the selected username."""
    src_root = Path(src_input)
    current_user = getpass.getuser()
        
    if not src_root.exists() or not src_root.is_dir():
        print(f"Error: Backup directory '{src_root}' not found or is not a valid directory.")
        return

    print("\nScanning for verified, completed backups...")
    
    available_users = []
    
    # Check every folder to see if it has a completed report
    for d in src_root.iterdir():
        if d.is_dir():
            # Find all reports in this user's folder
            reports = list(d.glob("backup_report_*.txt"))
            if reports:
                # Get the most recently created report
                latest_report = max(reports, key=lambda p: p.stat().st_mtime)
                try:
                    with open(latest_report, 'r', encoding='utf-8') as f:
                        if "[BACKUP COMPLETED SUCCESSFULLY]" in f.read():
                            available_users.append(d.name)
                except Exception:
                    pass
    
    if not available_users:
        print(f"\nNo fully completed user backups found in '{src_root}'.")
        print("(If a backup was interrupted, please run the backup process again to finish it).")
        return
        
    print("\nAvailable User Backups:")
    for i, user in enumerate(available_users, 1):
        print(f"{i}. {user}")
        
    while True:
        choice = input("\nEnter the number of the user you want to restore from: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(available_users):
                selected_user = available_users[idx]
                break
            else:
                print("Invalid selection. Please enter a valid number from the list.")
        except ValueError:
            print("Please enter a number.")

    src_base = src_root / selected_user

    print(f"\nStarting restore from backup '{selected_user}' to local user '{current_user}'")
    
    paths = get_os_paths()
    for cat, dst_path in paths.items():
        cat_backup_dir = src_base / cat
        if cat_backup_dir.exists():
            copy_with_progress(cat_backup_dir, dst_path, desc=f"Restoring {cat:<10}", rename_on_collision=True, recursive=True)
            
    user_backup_dir = src_base / 'user'
    if user_backup_dir.exists():
        home_path = Path.home()
        copy_with_progress(user_backup_dir, home_path, desc=f"Restoring {'user':<10}", rename_on_collision=True, recursive=False)
        
    print("\nRestore complete!")

def main():
    print("=== UniversalTransfer: Cross-Platform Backup & Restore ===")
    print("1. Backup current user files to an external drive")
    print("2. Restore files from an external drive to current user")
    print("3. Exit")
    
    choice = input("\nSelect an option (1/2/3): ").strip()
    
    if choice == '1':
        print("\nEnter the root destination path.")
        dest = input("Path (e.g., /Volumes/ExternalDrive/Backup): ").strip()
        backup(dest)
    elif choice == '2':
        print("\nEnter the root backup path.")
        print("(The program will scan this folder for valid users)")
        src = input("Path (e.g., /Volumes/ExternalDrive/Backup): ").strip()
        restore(src)
    elif choice == '3':
        sys.exit(0)
    else:
        print("Invalid selection.")

if __name__ == "__main__":
    main()