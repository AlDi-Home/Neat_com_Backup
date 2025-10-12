"""
Neat Backup Automation - GUI Application
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
from config import Config
from neat_bot import NeatBot

class NeatBackupGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.config = Config()
        self.bot = None
        self.backup_thread = None
        
        # Main window
        self.root = tk.Tk()
        self.root.title("Neat Backup Automation v1.0")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        self.create_widgets()
        self.load_saved_credentials()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Header
        header_frame = tk.Frame(self.root, bg='#515EDA', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="Neat Backup Automation",
            font=('Arial', 20, 'bold'),
            bg='#515EDA',
            fg='white'
        )
        title_label.pack(pady=25)
        
        # Main content frame
        content_frame = tk.Frame(self.root, padx=30, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Credentials section
        creds_frame = tk.LabelFrame(content_frame, text="Neat Credentials", font=('Arial', 11, 'bold'), padx=15, pady=15)
        creds_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(creds_frame, text="Username:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = tk.Entry(creds_frame, width=40, font=('Arial', 10))
        self.username_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        tk.Label(creds_frame, text="Password:", font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = tk.Entry(creds_frame, width=40, show='●', font=('Arial', 10))
        self.password_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        self.show_password_var = tk.BooleanVar()
        show_password_cb = tk.Checkbutton(
            creds_frame,
            text="Show password",
            variable=self.show_password_var,
            command=self.toggle_password
        )
        show_password_cb.grid(row=1, column=2, padx=(10, 0))
        
        self.save_creds_var = tk.BooleanVar(value=True)
        save_creds_cb = tk.Checkbutton(
            creds_frame,
            text="Remember credentials (encrypted)",
            variable=self.save_creds_var
        )
        save_creds_cb.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        # Settings section
        settings_frame = tk.LabelFrame(content_frame, text="Backup Settings", font=('Arial', 11, 'bold'), padx=15, pady=15)
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(settings_frame, text="Backup Folder:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        folder_input_frame = tk.Frame(settings_frame)
        folder_input_frame.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        self.backup_dir_var = tk.StringVar(value=self.config.get('download_dir'))
        backup_dir_entry = tk.Entry(folder_input_frame, textvariable=self.backup_dir_var, width=35, font=('Arial', 10))
        backup_dir_entry.pack(side=tk.LEFT)
        
        browse_btn = tk.Button(folder_input_frame, text="Browse...", command=self.browse_backup_dir)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        self.headless_var = tk.BooleanVar(value=self.config.get('chrome_headless', False))
        headless_cb = tk.Checkbutton(
            settings_frame,
            text="Run browser in background (headless mode)",
            variable=self.headless_var
        )
        headless_cb.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Status section
        status_frame = tk.LabelFrame(content_frame, text="Status", font=('Arial', 11, 'bold'), padx=15, pady=15)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Status log with scrollbar
        log_scroll = tk.Scrollbar(status_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_log = tk.Text(
            status_frame,
            height=12,
            width=70,
            font=('Courier', 9),
            yscrollcommand=log_scroll.set,
            state=tk.DISABLED
        )
        self.status_log.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.status_log.yview)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready to start backup...")
        progress_label = tk.Label(content_frame, textvariable=self.progress_var, font=('Arial', 10))
        progress_label.pack(pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(content_frame, mode='indeterminate', length=640)
        self.progress_bar.pack(pady=(0, 15))
        
        # Action buttons
        button_frame = tk.Frame(content_frame)
        button_frame.pack()
        
        self.start_btn = tk.Button(
            button_frame,
            text="Start Backup",
            command=self.start_backup,
            bg='#515EDA',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=15,
            height=2
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(
            button_frame,
            text="Stop",
            command=self.stop_backup,
            state=tk.DISABLED,
            font=('Arial', 11),
            width=15,
            height=2
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
    
    def toggle_password(self):
        """Toggle password visibility"""
        if self.show_password_var.get():
            self.password_entry.config(show='')
        else:
            self.password_entry.config(show='●')
    
    def browse_backup_dir(self):
        """Browse for backup directory"""
        directory = filedialog.askdirectory(
            initialdir=self.backup_dir_var.get(),
            title="Select Backup Directory"
        )
        if directory:
            self.backup_dir_var.set(directory)
    
    def load_saved_credentials(self):
        """Load saved credentials if available"""
        creds = self.config.load_credentials()
        if creds:
            self.username_entry.insert(0, creds[0])
            self.password_entry.insert(0, creds[1])
            self.log_status("Loaded saved credentials", "info")
    
    def log_status(self, message: str, level: str = 'info'):
        """Add message to status log"""
        self.status_log.config(state=tk.NORMAL)
        
        # Color coding
        tag = level
        if level == 'error':
            color = 'red'
        elif level == 'success':
            color = 'green'
        elif level == 'warning':
            color = 'orange'
        else:
            color = 'black'
        
        self.status_log.tag_config(tag, foreground=color)
        self.status_log.insert(tk.END, f"{message}\n", tag)
        self.status_log.see(tk.END)
        self.status_log.config(state=tk.DISABLED)
    
    def start_backup(self):
        """Start backup process"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        # Save credentials if requested
        if self.save_creds_var.get():
            self.config.save_credentials(username, password)
            self.log_status("Credentials saved (encrypted)", "success")
        
        # Update config
        self.config.set('download_dir', self.backup_dir_var.get())
        self.config.set('chrome_headless', self.headless_var.get())
        
        # Create backup directory
        Path(self.backup_dir_var.get()).mkdir(parents=True, exist_ok=True)
        
        # Disable start button, enable stop
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Start progress bar
        self.progress_bar.start()
        self.progress_var.set("Backup in progress...")
        
        # Clear log
        self.status_log.config(state=tk.NORMAL)
        self.status_log.delete(1.0, tk.END)
        self.status_log.config(state=tk.DISABLED)
        
        # Run backup in thread
        self.backup_thread = threading.Thread(
            target=self.run_backup_thread,
            args=(username, password),
            daemon=True
        )
        self.backup_thread.start()
    
    def run_backup_thread(self, username: str, password: str):
        """Run backup in background thread"""
        try:
            self.bot = NeatBot(self.config, status_callback=self.log_status)
            stats = self.bot.run_backup(username, password)
            
            # Show results
            self.root.after(0, lambda: self.backup_complete(stats))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_status(f"Backup failed: {str(e)}", "error"))
            self.root.after(0, self.backup_complete, {'success': False})
    
    def backup_complete(self, stats: dict):
        """Handle backup completion"""
        self.progress_bar.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if stats.get('success'):
            self.progress_var.set(f"Backup complete! {stats['total_files']} files from {stats['total_folders']} folders")
            messagebox.showinfo(
                "Backup Complete",
                f"Successfully exported {stats['total_files']} files from {stats['total_folders']} folders!\n\n"
                f"Location: {self.backup_dir_var.get()}"
            )
        else:
            self.progress_var.set("Backup failed - check log for details")
            messagebox.showerror("Backup Failed", "Backup process failed. Check the status log for details.")
    
    def stop_backup(self):
        """Stop backup process"""
        if self.bot:
            self.bot.cleanup()
        
        self.progress_bar.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_var.set("Backup stopped by user")
        self.log_status("Backup stopped by user", "warning")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = NeatBackupGUI()
    app.run()
