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
    └── /Your_Username/                         <-- 1. Auto-generated profile folder
        ├── backup_report_20260219_105933.txt   <-- 2. Live text log
        ├── Desktop/                            <-- 3. Category folders
        │   └── current_project.docx
        ├── Documents/
        │   ├── Finances/                       <-- 4. Inner contents preserved
        │   │   └── taxes_2025.xlsx
        │   └── resume.pdf
        ├── Downloads/
        ├── Music/
        ├── Pictures/
        ├── Videos/                             <-- 5. OS-standardized (e.g., macOS 'Movies')
        │   └── home_video.mp4
        └── user/                               <-- 6. Loose files from your home folder


## 🚀 Installation

1. Clone the repository to your local machine:
   ```bash
   git clone [https://github.com/Aoyi-Feng/UniversalTransfer.git](https://github.com/Aoyi-Feng/UniversalTransfer.git)
   cd UniversalTransfer
