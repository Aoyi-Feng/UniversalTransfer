import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import sys
import getpass
import platform
import shutil
from datetime import datetime
from pathlib import Path

# Import your existing script as the engine!
import main

# Set the overall theme and appearance
ctk.set_appearance_mode("System")  # Follows macOS/Linux dark or light mode
ctk.set_default_color_theme("blue")

class TextRedirector:
    """Redirects terminal print() statements to the GUI textbox."""
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, text):
        # Filter out the raw tqdm progress bar characters so they don't garble the text box
        if '\r' not in text:
            self.textbox.insert(ctk.END, text)
            self.textbox.see(ctk.END)

    def flush(self):
        pass

class UniversalTransferGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("UniversalTransfer")
        self.geometry("650x500")
        self.resizable(False, False)

        # Redirect standard output to our custom textbox
        self.console_textbox = None

        self.build_ui()

    def build_ui(self):
        # Title Label
        title_label = ctk.CTkLabel(self, text="UniversalTransfer", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(15, 5))

        # Tabview for Backup and Restore
        self.tabview = ctk.CTkTabview(self, width=600, height=200)
        self.tabview.pack(padx=20, pady=10)

        self.tabview.add("Backup")
        self.tabview.add("Restore")

        self.build_backup_tab()
        self.build_restore_tab()

        # Progress Bar (Indeterminate bouncing mode)
        self.progress_bar = ctk.CTkProgressBar(self, width=600, mode="indeterminate")
        self.progress_bar.pack(pady=(10, 5))
        self.progress_bar.set(0)

        # Console Output Textbox
        self.console_textbox = ctk.CTkTextbox(self, width=600, height=150, state="normal")
        self.console_textbox.pack(padx=20, pady=(0, 20))
        
        # Activate redirection
        sys.stdout = TextRedirector(self.console_textbox)

    def build_backup_tab(self):
        tab = self.tabview.tab("Backup")
        
        label = ctk.CTkLabel(tab, text="Select destination drive for your backup:")
        label.pack(anchor="w", padx=20, pady=(10, 0))

        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=10)

        self.backup_path_entry = ctk.CTkEntry(frame, width=400, placeholder_text="e.g., /Volumes/ExternalDrive/Backup")
        self.backup_path_entry.pack(side="left", padx=(0, 10))

        browse_btn = ctk.CTkButton(frame, text="Browse", width=80, command=self.browse_backup)
        browse_btn.pack(side="left")

        self.start_backup_btn = ctk.CTkButton(tab, text="Start Backup", command=self.start_backup_thread, fg_color="#28a745", hover_color="#218838")
        self.start_backup_btn.pack(pady=20)

    def build_restore_tab(self):
        tab = self.tabview.tab("Restore")
        
        label = ctk.CTkLabel(tab, text="Select the root backup folder to scan for users:")
        label.pack(anchor="w", padx=20, pady=(10, 0))

        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)

        self.restore_path_entry = ctk.CTkEntry(frame, width=310, placeholder_text="e.g., /Volumes/ExternalDrive/Backup")
        self.restore_path_entry.pack(side="left", padx=(0, 10))

        browse_btn = ctk.CTkButton(frame, text="Browse", width=80, command=self.browse_restore)
        browse_btn.pack(side="left", padx=(0, 10))

        scan_btn = ctk.CTkButton(frame, text="Scan", width=80, command=self.scan_for_users)
        scan_btn.pack(side="left")

        # Dropdown for available users
        self.user_dropdown = ctk.CTkOptionMenu(tab, values=["No users found yet..."], width=490)
        self.user_dropdown.pack(pady=10)

        self.start_restore_btn = ctk.CTkButton(tab, text="Start Restore", command=self.start_restore_thread, fg_color="#007bff", hover_color="#0056b3")
        self.start_restore_btn.pack(pady=5)

    def browse_backup(self):
        path = filedialog.askdirectory(title="Select Backup Destination")
        if path:
            self.backup_path_entry.delete(0, ctk.END)
            self.backup_path_entry.insert(0, path)

    def browse_restore(self):
        path = filedialog.askdirectory(title="Select Backup Root Directory")
        if path:
            self.restore_path_entry.delete(0, ctk.END)
            self.restore_path_entry.insert(0, path)

    def scan_for_users(self):
        src_root = Path(self.restore_path_entry.get().strip())
        if not src_root.exists() or not src_root.is_dir():
            messagebox.showerror("Error", "Please select a valid directory first.")
            return

        print(f"\nScanning '{src_root}' for verified backups...")
        available_users = []
        
        # Borrow the scanning logic from main.py
        for d in src_root.iterdir():
            if d.is_dir():
                reports = list(d.glob("backup_report_*.txt"))
                if reports:
                    latest_report = max(reports, key=lambda p: p.stat().st_mtime)
                    try:
                        with open(latest_report, 'r', encoding='utf-8') as f:
                            if "[BACKUP COMPLETED SUCCESSFULLY]" in f.read():
                                available_users.append(d.name)
                    except Exception:
                        pass

        if available_users:
            self.user_dropdown.configure(values=available_users)
            self.user_dropdown.set(available_users[0])
            print(f"Found {len(available_users)} available user profile(s).")
        else:
            self.user_dropdown.configure(values=["No valid backups found."])
            self.user_dropdown.set("No valid backups found.")
            print("No fully completed user backups found.")

    def start_backup_thread(self):
        dest = self.backup_path_entry.get().strip()
        if not dest:
            messagebox.showwarning("Warning", "Please select a destination first.")
            return

        self.start_backup_btn.configure(state="disabled")
        self.progress_bar.start()
        
        # Run in background to prevent GUI freezing
        thread = threading.Thread(target=self.run_backup_task, args=(dest,))
        thread.start()

    def run_backup_task(self, dest):
        try:
            # Call the exact backup function from your main.py!
            main.backup(dest)
        except Exception as e:
            print(f"\nCritical Error during backup: {e}")
        finally:
            self.progress_bar.stop()
            self.start_backup_btn.configure(state="normal")
            print("\n--- Task Finished ---")

    def start_restore_thread(self):
        src_root = self.restore_path_entry.get().strip()
        selected_user = self.user_dropdown.get()

        if not src_root or selected_user in ["No users found yet...", "No valid backups found."]:
            messagebox.showwarning("Warning", "Please select a valid root folder and user profile.")
            return

        self.start_restore_btn.configure(state="disabled")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self.run_restore_task, args=(src_root, selected_user))
        thread.start()

    def run_restore_task(self, src_root_str, selected_user):
        try:
            # We recreate the restore mapping logic here so we don't trigger main.py's terminal input()
            src_base = Path(src_root_str) / selected_user
            current_user = getpass.getuser()

            print(f"\nStarting restore from backup '{selected_user}' to local user '{current_user}'")
            
            paths = main.get_os_paths()
            for cat, dst_path in paths.items():
                cat_backup_dir = src_base / cat
                if cat_backup_dir.exists():
                    main.copy_with_progress(cat_backup_dir, dst_path, desc=f"Restoring {cat:<10}", rename_on_collision=True, recursive=True)
                    
            user_backup_dir = src_base / 'user'
            if user_backup_dir.exists():
                home_path = Path.home()
                main.copy_with_progress(user_backup_dir, home_path, desc=f"Restoring {'user':<10}", rename_on_collision=True, recursive=False)
                
            print("\nRestore complete!")

        except Exception as e:
            print(f"\nCritical Error during restore: {e}")
        finally:
            self.progress_bar.stop()
            self.start_restore_btn.configure(state="normal")
            print("\n--- Task Finished ---")

if __name__ == "__main__":
    app = UniversalTransferGUI()
    app.mainloop()