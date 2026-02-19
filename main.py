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
IGNORE_NAMES = {'thumbs.db', 'desktop.ini'}

def is_ignored(name):
    return name.startswith('.') or name.lower() in IGNORE_NAMES

def get_os_paths():
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
    total_size = 0
    try:
        for root, dirs, files in os.walk(directory):
            if not recursive:
                dirs[:] = []
            else:
                dirs[:] = [d for d in dirs if not is_ignored(d)]
            for f in files:
                if is_ignored(f): continue
                fp = Path(root) / f
                if fp.is_file() and not fp.is_symlink():
                    try: total_size += fp.stat().st_size
                    except OSError: pass
    except OSError: pass
    return total_size

def format_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"

def resolve_utlink(utlink_path, user_root):
    """Reads a .utlink file and returns the absolute path to the real backup file."""
    try:
        with open(utlink_path, 'r', encoding='utf-8') as f:
            target_rel_path = f.read().strip()
            return user_root / target_rel_path
    except Exception:
        return None

def copy_with_progress(src_dir, dst_dir, desc="Copying", rename_on_collision=False, recursive=True, mode="normal", user_root=None, prev_snapshot_name=None, category=""):
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    
    if not src_dir.exists(): return
    total_files = count_files(src_dir, recursive)
    if total_files == 0: return

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
                if is_ignored(file): continue 
                src_file = Path(root) / file
                if not src_file.is_file() or src_file.is_symlink(): continue

                try:
                    if mode == "backup":
                        dst_file = target_dir / file
                        matched_previous = False
                        
                        # --- POINTER CREATION LOGIC ---
                        if prev_snapshot_name and user_root:
                            rel_cat_path = Path(category) / rel_path / file
                            prev_file = user_root / prev_snapshot_name / rel_cat_path
                            prev_utlink = user_root / prev_snapshot_name / rel_cat_path.with_name(file + ".utlink")
                            
                            real_prev_file = None
                            link_content = None
                            
                            if prev_file.exists():
                                real_prev_file = prev_file
                                link_content = f"{prev_snapshot_name}/{rel_cat_path.as_posix()}"
                            elif prev_utlink.exists():
                                real_prev_file = resolve_utlink(prev_utlink, user_root)
                                try:
                                    with open(prev_utlink, 'r') as f:
                                        link_content = f.read().strip()
                                except: pass
                                    
                            if real_prev_file and real_prev_file.exists():
                                if os.path.getsize(src_file) == os.path.getsize(real_prev_file) and \
                                   os.path.getmtime(src_file) == os.path.getmtime(real_prev_file):
                                    matched_previous = True
                                    utlink_dst = target_dir / (file + ".utlink")
                                    with open(utlink_dst, 'w', encoding='utf-8') as f:
                                        f.write(link_content)
                                        
                        if not matched_previous:
                            shutil.copy2(src_file, dst_file)

                    elif mode == "restore":
                        # --- POINTER RESOLUTION LOGIC ---
                        is_utlink = file.endswith('.utlink')
                        actual_src_file = src_file
                        
                        if is_utlink:
                            dst_file = target_dir / src_file.with_suffix('').name
                            resolved = resolve_utlink(src_file, user_root)
                            if resolved and resolved.exists():
                                actual_src_file = resolved
                            else:
                                tqdm.write(f"Error: Broken pointer {src_file}")
                                pbar.update(1)
                                continue
                        else:
                            dst_file = target_dir / file

                        if rename_on_collision:
                            current_check = dst_file
                            counter = 1
                            already_restored = False
                            
                            while current_check.exists():
                                if os.path.getsize(actual_src_file) == os.path.getsize(current_check) and \
                                   os.path.getmtime(actual_src_file) == os.path.getmtime(current_check):
                                    already_restored = True
                                    break
                                current_check = target_dir / f"{dst_file.stem}_{counter}{dst_file.suffix}"
                                counter += 1
                                
                            if already_restored:
                                pbar.update(1)
                                continue 
                            dst_file = current_check
                            shutil.copy2(actual_src_file, dst_file)
                        else:
                            if not dst_file.exists() or os.path.getmtime(actual_src_file) > os.path.getmtime(dst_file):
                                shutil.copy2(actual_src_file, dst_file)
                                
                except PermissionError:
                    tqdm.write(f"Permission denied: Skipping {src_file}")
                except Exception as e:
                    tqdm.write(f"Error copying {src_file}: {e}")
                    
                pbar.update(1)

def backup(dest_input):
    username = getpass.getuser()
    user_root = Path(dest_input) / username
    user_root.mkdir(parents=True, exist_ok=True)
    
    # 1. Find the previous snapshot to compare against
    prev_snapshot_name = None
    if user_root.exists():
        snapshots = [d for d in user_root.iterdir() if d.is_dir()]
        valid_snapshots = []
        for s in snapshots:
            reports = list(s.glob("backup_report_*.txt"))
            if reports:
                try:
                    with open(max(reports, key=lambda p: p.stat().st_mtime), 'r', encoding='utf-8') as f:
                        if "[BACKUP COMPLETED SUCCESSFULLY]" in f.read():
                            valid_snapshots.append(s)
                except: pass
        if valid_snapshots:
            prev_snapshot_dir = max(valid_snapshots, key=lambda p: p.stat().st_mtime)
            prev_snapshot_name = prev_snapshot_dir.name
            print(f"\nFound previous snapshot: {prev_snapshot_name} (Will use pointers for unchanged files)")
    
    # 2. Setup the new snapshot directory
    current_time = datetime.now()
    snapshot_name = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    dest_base = user_root / snapshot_name
    dest_base.mkdir(parents=True, exist_ok=True)
    
    print(f"\nCalculating local size for user '{username}'...")
    total_local_size = 0
    folder_sizes = {} 
    
    paths = get_os_paths()
    for cat, src_path in paths.items():
        if src_path.exists():
            size = get_dir_size(src_path, recursive=True)
            folder_sizes[cat] = size
            total_local_size += size
            
    home_path = Path.home()
    user_loose_size = get_dir_size(home_path, recursive=False)
    folder_sizes['user'] = user_loose_size
    total_local_size += user_loose_size
            
    _, _, free_space = shutil.disk_usage(user_root)
    
    print(f"Total size to evaluate: {format_size(total_local_size)}")
    print(f"Available disk space:   {format_size(free_space)}")
    
    if total_local_size > free_space and not prev_snapshot_name:
        print("\nError: Not enough free space for initial full backup.")
        return
        
    print("\nStarting snapshot backup...")
    
    timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = current_time.strftime("%Y%m%d_%H%M%S")
    report_path = dest_base / f"backup_report_{file_timestamp}.txt"
    
    system_name = platform.node()
    os_type = f"{platform.system()} {platform.release()}"
    
    with open(report_path, "w") as report:
        report.write("=== CROSS-PLATFORM SNAPSHOT REPORT ===\n")
        report.write(f"Date/Time   : {timestamp_str}\n")
        report.write(f"User        : {username}\n")
        report.write(f"System Name : {system_name}\n")
        report.write(f"Source OS   : {os_type}\n")
        report.write(f"Snapshot ID : {snapshot_name}\n")
        report.write("-" * 50 + "\n")
        report.write(f"{'Category':<15} | {'Size evaluated':<14} | {'Status'}\n")
        report.write("-" * 50 + "\n")
        
        for cat, src_path in paths.items():
            if src_path.exists():
                size = folder_sizes[cat]
                copy_with_progress(src_path, dest_base / cat, desc=f"Evaluating {cat:<10}", recursive=True, mode="backup", user_root=user_root, prev_snapshot_name=prev_snapshot_name, category=cat)
                report.write(f"{cat:<15} | {format_size(size):<14} | Successfully processed\n")
            else:
                report.write(f"{cat:<15} | {'0.00 B':<14} | Skipped (Not found)\n")
                
        if user_loose_size > 0:
            copy_with_progress(home_path, dest_base / 'user', desc=f"Evaluating {'user':<10}", recursive=False, mode="backup", user_root=user_root, prev_snapshot_name=prev_snapshot_name, category="user")
            report.write(f"{'user (loose)':<15} | {format_size(user_loose_size):<14} | Successfully processed\n")
            
        report.write("-" * 50 + "\n")
        report.write("[BACKUP COMPLETED SUCCESSFULLY]\n")
        
    print(f"\nSnapshot complete! Saved in: {snapshot_name}")

def restore(src_input):
    src_root = Path(src_input)
    current_user = getpass.getuser()
        
    if not src_root.exists() or not src_root.is_dir():
        print(f"Error: Backup directory '{src_root}' not found.")
        return

    print("\nScanning for users...")
    available_users = [d.name for d in src_root.iterdir() if d.is_dir()]
    
    if not available_users:
        print(f"No users found in '{src_root}'.")
        return
        
    print("\nAvailable User Profiles:")
    for i, user in enumerate(available_users, 1):
        print(f"{i}. {user}")
        
    while True:
        choice = input("\nEnter the number of the user to restore from: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(available_users):
                selected_user = available_users[idx]
                break
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

    user_root = src_root / selected_user
    
    # --- SNAPSHOT SELECTION LOGIC ---
    print(f"\nScanning for valid snapshots for '{selected_user}'...")
    snapshots = []
    for d in user_root.iterdir():
        if d.is_dir():
            reports = list(d.glob("backup_report_*.txt"))
            if reports:
                try:
                    with open(max(reports, key=lambda p: p.stat().st_mtime), 'r', encoding='utf-8') as f:
                        if "[BACKUP COMPLETED SUCCESSFULLY]" in f.read():
                            snapshots.append(d.name)
                except: pass
                
    if not snapshots:
        print(f"No completed snapshots found for user '{selected_user}'.")
        return
        
    # Sort so the newest is at the top (index 0)
    snapshots.sort(reverse=True)
    
    print("\nAvailable Snapshots (Newest First):")
    for i, snap in enumerate(snapshots, 1):
        print(f"{i}. {snap}")
        
    while True:
        snap_choice = input(f"\nEnter the snapshot number to restore (Press Enter to default to latest: {snapshots[0]}): ").strip()
        if not snap_choice:
            selected_snapshot = snapshots[0]
            break
        try:
            snap_idx = int(snap_choice) - 1
            if 0 <= snap_idx < len(snapshots):
                selected_snapshot = snapshots[snap_idx]
                break
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number, or press Enter for the default.")

    src_base = user_root / selected_snapshot

    print(f"\nStarting restore from snapshot '{selected_snapshot}' to local user '{current_user}'...")
    
    paths = get_os_paths()
    for cat, dst_path in paths.items():
        cat_backup_dir = src_base / cat
        if cat_backup_dir.exists():
            copy_with_progress(cat_backup_dir, dst_path, desc=f"Restoring {cat:<10}", rename_on_collision=True, recursive=True, mode="restore", user_root=user_root)
            
    user_backup_dir = src_base / 'user'
    if user_backup_dir.exists():
        home_path = Path.home()
        copy_with_progress(user_backup_dir, home_path, desc=f"Restoring {'user':<10}", rename_on_collision=True, recursive=False, mode="restore", user_root=user_root)
        
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
        src = input("Path (e.g., /Volumes/ExternalDrive/Backup): ").strip()
        restore(src)
    elif choice == '3':
        sys.exit(0)
    else:
        print("Invalid selection.")

if __name__ == "__main__":
    main()