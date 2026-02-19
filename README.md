# UniversalTransfer

A cross-platform Python utility for backing up, restoring, and migrating user profiles between macOS and Linux. It handles OS-specific directory naming, filters system files, and uses a snapshot system for versioned backups.

## Features

* **Cross-Platform Mapping:** Translates directory paths between macOS and Linux (e.g., macOS `Movies` to Linux `Videos`).
* **Multi-User Support:** Isolates backups into specific `/[username]/` folders to allow multiple profiles on a single drive.
* **Incremental Snapshots:** Uses a `.utlink` text pointer system. Unchanged files generate a 1KB pointer to older backups instead of duplicating data.
* **Native Pointer Resolution:** Reads `.utlink` files via CLI and opens the original file using the OS default application.
* **Collision Protection:** Appends a counter (e.g., `file_1.txt`) during restore if a local file exists with the same name but different metadata.
* **System Filtering:** Ignores hidden files and specific system junk (`.DS_Store`, `thumbs.db`).
* **Validation:** Generates reports and requires a `[BACKUP COMPLETED SUCCESSFULLY]` tag to allow a folder to be restored.

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

