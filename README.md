# UniversalTransfer

A smart, cross-platform Python utility designed to seamlessly back up, restore, and migrate user profiles between macOS and Linux. UniversalTransfer intelligently handles OS-specific directory naming conventions, filters out system clutter, and protects your data integrity with automated validation checks.

## ✨ Features

* **Cross-Platform Routing:** Automatically translates directory paths between macOS and Linux (e.g., safely mapping macOS `Movies` to Linux `Videos`).
* **Multi-User Migration:** Isolates backups by username, allowing you to back up multiple computers to a single drive and interactively select which profile to restore.
* **Incremental & Resumable:** Saves time by only copying new or modified files. If a transfer is interrupted, it safely resumes exactly where it left off.
* **Non-Destructive Restores:** Protects local data by appending a counter (e.g., `file_1.txt`) if a naming collision occurs, ensuring existing files are never overwritten.
* **Pre-Flight Space Checks:** Calculates backup size and verifies available destination disk space before initiating transfers.
* **Clutter Filtering:** Automatically ignores hidden system files (`.DS_Store`, `.config`) and junk files (`thumbs.db`) to speed up transfers and save disk space.
* **Integrity Validation:** Generates timestamped reports and actively hides corrupted or interrupted backups from the restore menu.

---

## Directory Structure Example
    /Selected_Destination_Path/
    └── /Your_Username/
        │
        ├── /2026-02-18_10-00-00/                   <-- Initial Full Backup (Snapshot 1)
        │   ├── backup_report_20260218_100000.txt
        │   ├── Documents/
        │   │   ├── resume.pdf                      <-- Real, physical file (5 MB)
        │   │   └── finances.xlsx                   <-- Real, physical file (2 MB)
        │   └── Pictures/
        │       └── photo.jpg                       <-- Real, physical file (3 MB)
        │
        └── /2026-02-19_15-30-00/                   <-- Incremental Backup (Snapshot 2)
            ├── backup_report_20260219_153000.txt
            ├── Documents/
            │   ├── resume.pdf.utlink               <-- TEXT POINTER! (1 KB)
            │   ├── finances.xlsx.utlink            <-- TEXT POINTER! (1 KB)
            │   └── new_project.docx                <-- Real, newly created file (1 MB)
            └── Pictures/
                └── photo.jpg.utlink                <-- TEXT POINTER! (1 KB)


## 🚀 Installation

1. Clone the repository to your local machine:
   ```bash
   git clone [https://github.com/Aoyi-Feng/UniversalTransfer.git](https://github.com/Aoyi-Feng/UniversalTransfer.git)
   cd UniversalTransfer
