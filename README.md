# UniversalTransfer

A Python script to back up and restore standard user folders between macOS and Linux. It automatically maps the correct folder paths for each operating system (like mapping macOS `Movies` to Linux `Videos`).

## What It Does

* **Backs up** Documents, Pictures, Videos/Movies, Music, Desktop, and Downloads to a selected drive.
* **Restores** those files back to the correct user folders on either OS.
* **Skips** files that haven't changed to speed up future backups.
* **Checks** available disk space before starting.
* **Prevents overwriting** local files during a restore by adding a number to the filename (e.g., `file_1.txt`) if there is a conflict.
* **Logs** the backup details and folder sizes to a `.txt` file.

## How to Use

1. Download the code:
   ```bash
   git clone [https://github.com/Aoyi-Feng/UniversalTransfer.git](https://github.com/Aoyi-Feng/UniversalTransfer.git)
   cd UniversalTransfer
