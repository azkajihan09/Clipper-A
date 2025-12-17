# ============================================================================
# SmartClip AI - Multi-Platform Batch Optimizer
# Optimize multiple videos for different social media platforms at once
# ============================================================================

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from video_processor import VideoProcessor, PlatformOptimizer
import threading
import time

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class BatchOptimizerApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("SmartClip AI - Batch Platform Optimizer")
        self.root.geometry("800x600")
        
        self.video_files = []
        self.selected_platforms = []
        self.output_directory = ""
        self.is_processing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="🚀 Batch Platform Optimizer", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 30))
        
        # Video files section
        video_frame = ctk.CTkFrame(main_frame)
        video_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(video_frame, text="📁 Video Files", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        video_btn_frame = ctk.CTkFrame(video_frame, fg_color="transparent")
        video_btn_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkButton(video_btn_frame, text="Add Videos", 
                      command=self.add_videos, width=120).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(video_btn_frame, text="Clear All", 
                      command=self.clear_videos, width=100).pack(side="left")
        
        # Video list
        self.video_listbox = tk.Listbox(video_frame, height=6)
        self.video_listbox.pack(fill="x", padx=20, pady=(0, 20))
        
        # Platform selection
        platform_frame = ctk.CTkFrame(main_frame)
        platform_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(platform_frame, text="📱 Target Platforms", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Platform checkboxes in grid
        self.platform_vars = {}
        platform_grid = ctk.CTkFrame(platform_frame, fg_color="transparent")
        platform_grid.pack(fill="x", padx=20, pady=(0, 20))
        
        platforms = PlatformOptimizer.get_platform_list()
        for i, platform in enumerate(platforms):
            var = ctk.BooleanVar()
            self.platform_vars[platform] = var
            
            row = i // 3
            col = i % 3
            
            checkbox = ctk.CTkCheckBox(platform_grid, text=platform, variable=var,
                                       command=self.update_selected_platforms)
            checkbox.grid(row=row, column=col, padx=10, pady=5, sticky="w")
        
        # Output directory
        output_frame = ctk.CTkFrame(main_frame)
        output_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(output_frame, text="📁 Output Directory", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        output_btn_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_btn_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkButton(output_btn_frame, text="Select Folder", 
                      command=self.select_output_dir, width=120).pack(side="left", padx=(0, 10))
        
        self.output_label = ctk.CTkLabel(output_btn_frame, text="No folder selected")
        self.output_label.pack(side="left")
        
        # Progress section
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="Ready to process")
        self.progress_label.pack(pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_bar.set(0)
        
        # Control buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        self.start_btn = ctk.CTkButton(btn_frame, text="🚀 Start Batch Optimization", 
                                       command=self.start_processing, 
                                       font=ctk.CTkFont(size=16, weight="bold"),
                                       height=40, fg_color="#10B981")
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        self.stop_btn = ctk.CTkButton(btn_frame, text="⏹️ Stop", 
                                      command=self.stop_processing,
                                      height=40, fg_color="#EF4444", state="disabled")
        self.stop_btn.pack(side="right")
        
    def add_videos(self):
        files = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv"),
                ("All files", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.video_files:
                self.video_files.append(file)
                self.video_listbox.insert(tk.END, os.path.basename(file))
    
    def clear_videos(self):
        self.video_files.clear()
        self.video_listbox.delete(0, tk.END)
    
    def update_selected_platforms(self):
        self.selected_platforms = [platform for platform, var in self.platform_vars.items() 
                                   if var.get()]
    
    def select_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_directory = directory
            self.output_label.configure(text=os.path.basename(directory))
    
    def start_processing(self):
        if not self.video_files:
            messagebox.showerror("Error", "Please add at least one video file")
            return
        
        if not self.selected_platforms:
            messagebox.showerror("Error", "Please select at least one platform")
            return
        
        if not self.output_directory:
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        self.is_processing = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_videos)
        thread.daemon = True
        thread.start()
    
    def stop_processing(self):
        self.is_processing = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_label.configure(text="Processing stopped")
    
    def process_videos(self):
        try:
            processor = VideoProcessor(output_dir=self.output_directory)
            
            total_jobs = len(self.video_files) * len(self.selected_platforms)
            completed_jobs = 0
            
            for video_file in self.video_files:
                if not self.is_processing:
                    break
                
                video_name = os.path.splitext(os.path.basename(video_file))[0]
                
                # Create subdirectory for this video
                video_output_dir = os.path.join(self.output_directory, video_name)
                os.makedirs(video_output_dir, exist_ok=True)
                
                for platform in self.selected_platforms:
                    if not self.is_processing:
                        break
                    
                    # Update progress
                    progress = completed_jobs / total_jobs
                    self.progress_bar.set(progress)
                    self.progress_label.configure(text=f"Processing {video_name} for {platform}...")
                    self.root.update()
                    
                    # Process video for platform
                    platform_safe = platform.replace(" ", "_").replace("/", "_")
                    output_filename = f"{video_name}_{platform_safe}.mp4"
                    output_path = os.path.join(video_output_dir, output_filename)
                    
                    def progress_callback(msg):
                        if self.is_processing:
                            self.progress_label.configure(text=f"{msg}")
                            self.root.update()
                    
                    result = processor.optimize_for_platform(
                        video_file, 
                        platform,
                        output_path=output_path,
                        progress_callback=progress_callback
                    )
                    
                    completed_jobs += 1
                    
                    if result:
                        print(f"✅ Completed: {output_filename}")
                    else:
                        print(f"❌ Failed: {output_filename}")
            
            # Final update
            if self.is_processing:
                self.progress_bar.set(1.0)
                self.progress_label.configure(text=f"✅ Batch processing completed! {completed_jobs}/{total_jobs} successful")
                messagebox.showinfo("Complete", f"Batch processing finished!\n{completed_jobs}/{total_jobs} videos processed successfully.")
            
            self.is_processing = False
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
            self.is_processing = False
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = BatchOptimizerApp()
    app.run()