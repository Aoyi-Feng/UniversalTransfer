import os
import sys
import shutil
import platform
from datetime import datetime
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    print("Error: The 'tqdm' library is required for progress bars.")
    print("Please install it by running: pip install tqdm")
    sys.exit(1)

CATEGORIES = ['Documents', 'Pictures', 'Videos', 'Music', 'Desktop', 'Downloads']

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

def count_files(directory):
    """Counts total files, completely ignoring hidden/system files."""
    count = 0
    for root, dirs, files in os.walk(directory):
        # Prevent os.walk from even entering hidden directories
        dirs[:] = [d for d in dirs if not is_ignored(d)]
        # Only count non-ignored files
        files = [f for f in files if not is_ignored(f)]
        count += len(files)
    return count

def get_dir_size(directory):
    """Calculates total size, completely ignoring hidden/system files."""
    total_size = 0
    try:
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not is_ignored(d)]
            for f in files:
                if is_ignored(f):
                    continue
                fp = Path(root) / f
                if not fp.is_symlink():
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

def copy_with_progress(src_dir, dst_dir, desc="Copying", rename_on_collision=False):
    """Copies files recursively, skipping hidden and system files."""
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    
    if not src_dir.exists():
        return
        
    total_files = count_files(src_dir)
    if total_files == 0:
        return

    with tqdm(total_files=total_files, desc=desc, unit="file", leave=True) as pbar:
        for root, dirs, files in os.walk(src_dir):
            # Prevent entering hidden directories
            dirs[:] = [d for d in dirs if not is_ignored(d)]
            
            rel_path = Path(root).relative_to(src_dir)
            target_dir = dst_dir / rel_path
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for file in files:
                if is_ignored(file):
                    continue # Skip the hidden/system file completely
                    
                src_file = Path(root) / file
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

def backup(dest_base):
    """Backs up local user folders to the target directory and creates a log."""
    paths = get_os_paths()
    dest_base = Path(dest_base)
    dest_base.mkdir(parents=True, exist_ok=True)
    
    print("\nCalculating backup size...")
    total_backup_size = 0
    folder_sizes = {} 
    
    for cat, src_path in paths.items():
        if src_path.exists():
            size = get_dir_size(src_path)
            folder_sizes[cat] = size
            total_backup_size += size
            
    # Check available disk space
    _, _, free_space = shutil.disk_usage(dest_base)
    
    print(f"Total backup size: {format_size(total_backup_size)}")
    print(f"Available space:   {format_size(free_space)}")
    
    if total_backup_size > free_space:
        print("\nError: Not enough free space on the destination drive.")
        print("Backup aborted.")
        return
        
    print("\nSpace check passed. Starting backup...")
    
    # Setup reporting variables
    current_time = datetime.now()
    timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = current_time.strftime("%Y%m%d_%H%M%S")
    report_path = dest_base / f"backup_report_{file_timestamp}.txt"
    
    with open(report_path, "w") as report:
        report.write("=== CROSS-PLATFORM BACKUP REPORT ===\n")
        report.write(f"Date/Time : {timestamp_str}\n")
        report.write(f"Source OS : {platform.system()}\n")
        report.write(f"Target Dir: {dest_base}\n")
        report.write("-" * 50 + "\n")
        report.write(f"{'Category':<15} | {'Size':<12} | {'Status'}\n")
        report.write("-" * 50 + "\n")
        
        for cat, src_path in paths.items():
            if src_path.exists():
                size = folder_sizes[cat]
                formatted_size = format_size(size)
                
                # Rename is False for backups (default)
                copy_with_progress(src_path, dest_base / cat, desc=f"Backing up {cat:<10}")
                report.write(f"{cat:<15} | {formatted_size:<12} | Successfully backed up\n")
            else:
                report.write(f"{cat:<15} | {'0.00 B':<12} | Skipped (Folder not found)\n")
                
        report.write("-" * 50 + "\n")
        report.write(f"Total Backup Size Processed: {format_size(total_backup_size)}\n")
        
    print(f"\nBackup complete! Report saved to: {report_path}")

def restore(src_base):
    """Restores folders from the backup directory to the local user folders."""
    paths = get_os_paths()
    src_base = Path(src_base)
    
    if not src_base.exists():
        print(f"Error: Backup directory '{src_base}' not found.")
        return

    print(f"\nStarting restore from: {src_base}")
    for cat, dst_path in paths.items():
        cat_backup_dir = src_base / cat
        if cat_backup_dir.exists():
            # Rename is True for restores to prevent accidental overwrites
            copy_with_progress(cat_backup_dir, dst_path, desc=f"Restoring {cat:<10}", rename_on_collision=True)
    print("\nRestore complete!")

def main():
    print("=== UniversalTransfer: Cross-Platform Backup & Restore ===")
    print("1. Backup current user files to an external drive")
    print("2. Restore files from an external drive to current user")
    print("3. Exit")
    
    choice = input("\nSelect an option (1/2/3): ").strip()
    
    if choice == '1':
        dest = input("Enter the destination path (e.g., /Volumes/ExternalDrive/Backup): ").strip()
        backup(dest)
    elif choice == '2':
        src = input("Enter the source backup path (e.g., /media/user/ExternalDrive/Backup): ").strip()
        restore(src)
    elif choice == '3':
        sys.exit(0)
    else:
        print("Invalid selection.")

if __name__ == "__main__":
    main()