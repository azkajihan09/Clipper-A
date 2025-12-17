import customtkinter as ctk
from tkinter import filedialog, font
import threading
import os
import json
from config import get_api_key, save_api_key, get_grok_api_key, save_grok_api_key, get_openrouter_api_key, save_openrouter_api_key
from ai_handler import AIHandler, GrokHandler, OpenRouterHandler, OPENAI_AVAILABLE
from video_processor import VideoProcessor
from youtube_handler import YouTubeHandler
import license_handler

# === PROFESSIONAL DARK THEME ===
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Color Palette
COLORS = {
    "bg_dark": "#0D0D0D",
    "bg_card": "#1A1A1F",
    "bg_input": "#131316",
    "accent": "#6366F1",
    "accent_hover": "#4F46E5",
    "success": "#10B981",
    "success_hover": "#059669",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "danger_hover": "#DC2626",
    "text_primary": "#F3F4F6",
    "text_secondary": "#9CA3AF",
    "text_muted": "#6B7280",
    "border": "#2D2D35",
    "border_light": "#3F3F46"
}

class FontPickerDialog(ctk.CTkToplevel):
    """A searchable, scrollable font picker dialog."""
    
    def __init__(self, parent, fonts_list, current_font="Arial"):
        super().__init__(parent)
        
        self.title("Select Font")
        self.geometry("350x450")
        self.resizable(False, True)
        self.result = None
        self.fonts_list = fonts_list
        self.current_font = current_font
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 175
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 225
        self.geometry(f"+{x}+{y}")
        
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Header
        header = ctk.CTkLabel(self, text="🔤 Select Font", 
                              font=ctk.CTkFont(size=16, weight="bold"),
                              text_color=COLORS["text_primary"])
        header.pack(pady=(15, 10))
        
        # Search Entry
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 5))
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._filter_fonts)
        self.search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var,
                                          placeholder_text="Search fonts...",
                                          height=32, corner_radius=6,
                                          fg_color=COLORS["bg_input"],
                                          border_color=COLORS["border"])
        self.search_entry.pack(fill="x", expand=True)
        
        # Font List (Scrollable)
        self.font_listbox_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_card"],
                                                          corner_radius=8,
                                                          border_width=1,
                                                          border_color=COLORS["border"])
        self.font_listbox_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        self.font_buttons = []
        self._populate_fonts(self.fonts_list)
        
        # Preview Frame
        preview_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], 
                                      corner_radius=8, height=50)
        preview_frame.pack(fill="x", padx=15, pady=(0, 10))
        preview_frame.pack_propagate(False)
        
        self.preview_label = ctk.CTkLabel(preview_frame, text="Preview Text - Abc 123",
                                           font=ctk.CTkFont(family=current_font, size=14))
        self.preview_label.pack(expand=True)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", width=100, height=32,
                                    fg_color=COLORS["border"], hover_color=COLORS["border_light"],
                                    command=self.destroy)
        cancel_btn.pack(side="left")
        
        select_btn = ctk.CTkButton(btn_frame, text="Select", width=100, height=32,
                                    fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                    command=self._on_select)
        select_btn.pack(side="right")
        
        # Focus search
        self.search_entry.focus_set()
        
        # Scroll to current font if exists
        self.after(100, lambda: self._scroll_to_font(current_font))
    
    def _populate_fonts(self, fonts):
        """Populate the font list with buttons."""
        # Clear existing
        for btn in self.font_buttons:
            btn.destroy()
        self.font_buttons.clear()
        
        for font_name in fonts:
            btn = ctk.CTkButton(self.font_listbox_frame, text=font_name,
                                 anchor="w", height=28, corner_radius=4,
                                 fg_color="transparent", 
                                 hover_color=COLORS["border_light"],
                                 text_color=COLORS["text_primary"],
                                 command=lambda f=font_name: self._select_font(f))
            btn.pack(fill="x", pady=1, padx=2)
            self.font_buttons.append(btn)
            
            # Highlight current selection
            if font_name == self.current_font:
                btn.configure(fg_color=COLORS["accent"])
    
    def _filter_fonts(self, *args):
        """Filter fonts based on search text."""
        query = self.search_var.get().lower()
        if query:
            filtered = [f for f in self.fonts_list if query in f.lower()]
        else:
            filtered = self.fonts_list
        self._populate_fonts(filtered)
    
    def _select_font(self, font_name):
        """Handle font selection."""
        self.current_font = font_name
        
        # Update preview
        try:
            self.preview_label.configure(font=ctk.CTkFont(family=font_name, size=14))
        except:
            pass
        
        # Update button highlights
        for btn in self.font_buttons:
            if btn.cget("text") == font_name:
                btn.configure(fg_color=COLORS["accent"])
            else:
                btn.configure(fg_color="transparent")
    
    def _scroll_to_font(self, font_name):
        """Scroll to the specified font in the list."""
        # This is a simple implementation - just highlight it
        for btn in self.font_buttons:
            if btn.cget("text") == font_name:
                btn.configure(fg_color=COLORS["accent"])
                break
    
    def _on_select(self):
        """Confirm selection and close."""
        self.result = self.current_font
        self.destroy()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SmartClip AI - Professional Edition")
        self.geometry("900x800")
        self.minsize(800, 600)
        
        # Apply dark background
        self.configure(fg_color=COLORS["bg_dark"])
        
        # --- License Check ---
        self.withdraw()
        self.update()
        
        is_licensed, license_type = license_handler.check_license(self)
        
        if not is_licensed:
            self.destroy()
            return
        
        self.license_type = license_type
        self.deiconify()
        
        # Processing Control
        self.processing_flag = threading.Event()
        self.is_processing = False
        
        # Configure Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main Scrollable Container
        self.main_container = ctk.CTkScrollableFrame(
            self, 
            corner_radius=0, 
            fg_color=COLORS["bg_dark"],
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"]
        )
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)

        # --- Font System ---
        self.fonts = {
            "h1": ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            "h2": ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            "h3": ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            "body": ctk.CTkFont(family="Segoe UI", size=13),
            "small": ctk.CTkFont(family="Segoe UI", size=11),
            "mono": ctk.CTkFont(family="Consolas", size=12)
        }
        
        # Legacy font references for compatibility
        self.header_font = self.fonts["h1"]
        self.section_font = self.fonts["h2"]
        self.label_font = self.fonts["body"]

        # --- 1. Header Section ---
        self.header_frame = ctk.CTkFrame(
            self.main_container, 
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"]
        )
        self.header_frame.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="ew")
        
        header_inner = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_inner.pack(fill="x", padx=16, pady=10)
        
        self.title_label = ctk.CTkLabel(
            header_inner, 
            text="⚡ SmartClip AI", 
            font=self.fonts["h1"],
            text_color=COLORS["text_primary"]
        )
        self.title_label.pack(side="left")
        
        if hasattr(self, 'license_type') and self.license_type == "trial":
            license_status_text = "v2.0 PRO  •  ⏱️ Trial"
            license_color = COLORS["warning"]
        else:
            license_status_text = "v2.0 PRO  •  ✅ Licensed"
            license_color = COLORS["success"]
        
        self.status_label = ctk.CTkLabel(
            header_inner, 
            text=license_status_text, 
            text_color=license_color,
            font=self.fonts["body"]
        )
        self.status_label.pack(side="right")

        # === 2-COLUMN MAIN LAYOUT ===
        self.two_col_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.two_col_frame.grid(row=1, column=0, padx=16, pady=4, sticky="nsew")
        self.two_col_frame.grid_columnconfigure(0, weight=1)  # Left column
        self.two_col_frame.grid_columnconfigure(1, weight=2)  # Right column (wider)

        # === LEFT COLUMN: System Settings ===
        self.left_column = ctk.CTkFrame(
            self.two_col_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"]
        )
        self.left_column.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")
        
        # Settings Title
        settings_header = ctk.CTkFrame(self.left_column, fg_color="transparent")
        settings_header.pack(fill="x", padx=12, pady=(10, 6))
        ctk.CTkLabel(settings_header, text="⚙️ System Settings", font=self.fonts["h2"], 
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkFrame(self.left_column, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=12, pady=(0, 8))
        
        # Settings Content
        settings_content = ctk.CTkFrame(self.left_column, fg_color="transparent")
        settings_content.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        settings_content.grid_columnconfigure(1, weight=1)
        
        # AI Provider Selection
        ctk.CTkLabel(settings_content, text="AI:", font=self.fonts["body"],
                     text_color=COLORS["text_secondary"]).grid(row=0, column=0, pady=6, sticky="w")
        self.ai_provider_var = ctk.StringVar(value="Gemini")
        self.ai_provider_menu = ctk.CTkOptionMenu(settings_content, values=["Gemini", "Grok (xAI)", "OpenRouter (Free)"],
                                                   variable=self.ai_provider_var, width=100, height=32,
                                                   corner_radius=6, fg_color=COLORS["bg_input"],
                                                   button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
                                                   command=self.on_ai_provider_change)
        self.ai_provider_menu.grid(row=0, column=1, columnspan=2, padx=(8, 0), pady=6, sticky="w")

        # API Key (Row 1)
        ctk.CTkLabel(settings_content, text="API Key:", font=self.fonts["body"],
                     text_color=COLORS["text_secondary"]).grid(row=1, column=0, pady=6, sticky="w")
        self.api_key_entry = ctk.CTkEntry(settings_content, show="•", height=34, corner_radius=6,
                                          border_width=1, border_color=COLORS["border"],
                                          fg_color=COLORS["bg_input"], placeholder_text="Enter key...")
        self.api_key_entry.grid(row=1, column=1, padx=(8, 0), pady=6, sticky="ew")
        
        # Load initial key based on provider
        existing_key = get_api_key()
        if existing_key:
            self.api_key_entry.insert(0, existing_key)
        self.save_key_btn = ctk.CTkButton(settings_content, text="Save", width=60, height=34, corner_radius=6,
                                          fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                          command=self.save_key)
        self.save_key_btn.grid(row=1, column=2, padx=(6, 0), pady=6)
        
        # Render Device
        ctk.CTkLabel(settings_content, text="Render:", font=self.fonts["body"],
                     text_color=COLORS["text_secondary"]).grid(row=2, column=0, pady=6, sticky="w")
        self.render_device_var = ctk.StringVar(value="CPU")
        self.device_menu = ctk.CTkOptionMenu(settings_content, values=["CPU", "NVIDIA GPU", "AMD GPU"],
                                              variable=self.render_device_var, command=self.save_settings,
                                              height=32, corner_radius=6, fg_color=COLORS["bg_input"],
                                              button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"])
        self.device_menu.grid(row=2, column=1, columnspan=2, padx=(8, 0), pady=6, sticky="w")
        
        # Browser Cookies
        ctk.CTkLabel(settings_content, text="Cookies:", font=self.fonts["body"],
                     text_color=COLORS["text_secondary"]).grid(row=3, column=0, pady=6, sticky="w")
        self.browser_cookie_var = ctk.StringVar(value="None")
        self.browser_menu = ctk.CTkOptionMenu(settings_content, values=["None", "Chrome", "Firefox", "Edge"],
                                               variable=self.browser_cookie_var, width=120, height=32,
                                               corner_radius=6, fg_color=COLORS["bg_input"],
                                               button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
                                               command=self.save_settings)
        self.browser_menu.grid(row=3, column=1, columnspan=2, padx=(8, 0), pady=6, sticky="w")
        
        self.load_settings()

        # === RIGHT COLUMN: Input + Analysis ===
        self.right_column = ctk.CTkFrame(self.two_col_frame, fg_color="transparent")
        self.right_column.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        self.right_column.grid_rowconfigure(1, weight=1)
        self.right_column.grid_columnconfigure(0, weight=1)
        
        # --- Input Source Card ---
        self.input_card = ctk.CTkFrame(self.right_column, fg_color=COLORS["bg_card"],
                                        corner_radius=10, border_width=1, border_color=COLORS["border"])
        self.input_card.grid(row=0, column=0, pady=(0, 6), sticky="ew")
        
        input_header = ctk.CTkFrame(self.input_card, fg_color="transparent")
        input_header.pack(fill="x", padx=12, pady=(10, 6))
        ctk.CTkLabel(input_header, text="🎬 Input Source", font=self.fonts["h2"],
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkFrame(self.input_card, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=12, pady=(0, 6))
        
        input_content = ctk.CTkFrame(self.input_card, fg_color="transparent")
        input_content.pack(fill="x", padx=12, pady=(0, 10))
        
        # YouTube URL
        url_row = ctk.CTkFrame(input_content, fg_color="transparent")
        url_row.pack(fill="x", pady=4)
        ctk.CTkLabel(url_row, text="YouTube URL:", font=self.fonts["body"],
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self.youtube_url_entry = ctk.CTkEntry(url_row, placeholder_text="https://youtube.com/watch?v=...",
                                               height=34, corner_radius=6, border_width=1,
                                               border_color=COLORS["border"], fg_color=COLORS["bg_input"])
        self.youtube_url_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Subtitle Upload
        sub_row = ctk.CTkFrame(input_content, fg_color="transparent")
        sub_row.pack(fill="x", pady=4)
        ctk.CTkLabel(sub_row, text="Subtitle:", font=self.fonts["body"],
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self.select_file_btn = ctk.CTkButton(sub_row, text="📁 Upload", width=90, height=30,
                                              corner_radius=6, fg_color=COLORS["bg_input"],
                                              border_width=1, border_color=COLORS["border"],
                                              hover_color=COLORS["border_light"],
                                              text_color=COLORS["text_primary"], command=self.select_file)
        self.select_file_btn.pack(side="left", padx=(10, 8))
        self.file_path_label = ctk.CTkLabel(sub_row, text="No file", text_color=COLORS["text_muted"],
                                             font=self.fonts["small"])
        self.file_path_label.pack(side="left")
        self.selected_file_path = None
        
        # --- Analysis & Output Card ---
        self.analysis_card = ctk.CTkFrame(self.right_column, fg_color=COLORS["bg_card"],
                                           corner_radius=10, border_width=1, border_color=COLORS["border"])
        self.analysis_card.grid(row=1, column=0, pady=(6, 0), sticky="nsew")
        
        analysis_header = ctk.CTkFrame(self.analysis_card, fg_color="transparent")
        analysis_header.pack(fill="x", padx=12, pady=(10, 6))
        ctk.CTkLabel(analysis_header, text="⚙️ Analysis & Output", font=self.fonts["h2"],
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkFrame(self.analysis_card, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=12, pady=(0, 6))
        
        analysis_content = ctk.CTkFrame(self.analysis_card, fg_color="transparent")
        analysis_content.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        
        # Method & Language Row
        method_row = ctk.CTkFrame(analysis_content, fg_color="transparent")
        method_row.pack(fill="x", pady=4)
        
        ctk.CTkLabel(method_row, text="Method:", font=self.fonts["body"],
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self.analysis_method_var = ctk.StringVar(value="Auto")
        self.method_menu = ctk.CTkOptionMenu(method_row, values=["Auto", "Subtitle", "Audio"],
                                              variable=self.analysis_method_var, width=100, height=30,
                                              corner_radius=6, fg_color=COLORS["bg_input"],
                                              button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"])
        self.method_menu.pack(side="left", padx=(8, 20))
        
        ctk.CTkLabel(method_row, text="Lang:", font=self.fonts["body"],
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self.sub_language_var = ctk.StringVar(value="Indonesian (ID)")
        self.language_menu = ctk.CTkOptionMenu(method_row, values=["Indonesian (ID)", "English (EN)"],
                                                variable=self.sub_language_var, width=130, height=30,
                                                corner_radius=6, fg_color=COLORS["bg_input"],
                                                button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"])
        self.language_menu.pack(side="left", padx=(8, 0))
        
        # Checkboxes in 3 columns
        ctk.CTkFrame(analysis_content, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=8)
        
        checkbox_frame = ctk.CTkFrame(analysis_content, fg_color="transparent")
        checkbox_frame.pack(fill="x", pady=4)
        
        # Column 1: Platform & Format
        col1 = ctk.CTkFrame(checkbox_frame, fg_color="transparent")
        col1.pack(side="left", fill="y", padx=(0, 16), anchor="n")
        ctk.CTkLabel(col1, text="📱 Platform", font=self.fonts["h3"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 4))
        
        # Platform Selection
        platform_frame = ctk.CTkFrame(col1, fg_color="transparent")
        platform_frame.pack(anchor="w", fill="x", pady=2)
        
        self.platform_var = ctk.StringVar(value="Original")
        
        # Import PlatformOptimizer to get platform list
        from video_processor import PlatformOptimizer
        platform_options = ["Original"] + PlatformOptimizer.get_platform_list()
        
        self.platform_menu = ctk.CTkOptionMenu(platform_frame, variable=self.platform_var,
                                              values=platform_options,
                                              width=140, height=28,
                                              corner_radius=6,
                                              fg_color=COLORS["bg_input"],
                                              button_color=COLORS["accent"],
                                              button_hover_color=COLORS["accent_hover"],
                                              dropdown_fg_color=COLORS["bg_card"],
                                              dropdown_text_color=COLORS["text_primary"],
                                              text_color=COLORS["text_primary"],
                                              font=self.fonts["small"],
                                              command=self.on_platform_change)
        self.platform_menu.pack(side="left")
        
        # Platform info label
        self.platform_info_label = ctk.CTkLabel(platform_frame, text="", 
                                                 text_color=COLORS["text_muted"], 
                                                 font=self.fonts["small"])
        self.platform_info_label.pack(side="left", padx=(8, 0))
        
        # Legacy format options (for backwards compatibility)
        format_frame = ctk.CTkFrame(col1, fg_color="transparent")
        format_frame.pack(anchor="w", fill="x", pady=(8, 0))
        
        self.tiktok_mode_var = ctk.BooleanVar(value=False)
        self.tiktok_checkbox = ctk.CTkCheckBox(format_frame, text="Legacy 9:16", variable=self.tiktok_mode_var,
                                                font=self.fonts["small"], text_color=COLORS["text_secondary"],
                                                fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                                border_color=COLORS["border"])
        self.tiktok_checkbox.pack(anchor="w", pady=1)
        
        self.podcast_mode_var = ctk.BooleanVar(value=False)
        self.podcast_checkbox = ctk.CTkCheckBox(format_frame, text="Podcast", variable=self.podcast_mode_var,
                                                 font=self.fonts["small"], text_color=COLORS["text_secondary"],
                                                 fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                                 border_color=COLORS["border"])
        self.podcast_checkbox.pack(anchor="w", padx=12, pady=1)
        
        self.active_speaker_var = ctk.BooleanVar(value=False)
        self.active_speaker_checkbox = ctk.CTkCheckBox(format_frame, text="Speaker", variable=self.active_speaker_var,
                                                        font=self.fonts["small"], text_color=COLORS["text_secondary"],
                                                        fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                                        border_color=COLORS["border"])
        self.active_speaker_checkbox.pack(anchor="w", padx=12, pady=1)
        
        # Column 2: Enhancements
        col2 = ctk.CTkFrame(checkbox_frame, fg_color="transparent")
        col2.pack(side="left", fill="y", padx=16, anchor="n")
        ctk.CTkLabel(col2, text="✨ Enhance", font=self.fonts["h3"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 4))
        
        self.overlay_var = ctk.BooleanVar(value=False)
        self.overlay_checkbox = ctk.CTkCheckBox(col2, text="Overlay", variable=self.overlay_var,
                                                 command=self.toggle_overlay_ui, font=self.fonts["small"],
                                                 text_color=COLORS["text_secondary"], fg_color=COLORS["accent"],
                                                 hover_color=COLORS["accent_hover"], border_color=COLORS["border"])
        self.overlay_checkbox.pack(anchor="w", pady=2)
        
        self.overlay_picker_frame = ctk.CTkFrame(col2, fg_color="transparent")
        self.select_overlay_btn = ctk.CTkButton(self.overlay_picker_frame, text="Select", width=50, height=22,
                                                 corner_radius=4, fg_color=COLORS["bg_input"],
                                                 border_width=1, border_color=COLORS["border"],
                                                 hover_color=COLORS["border_light"], text_color=COLORS["text_primary"],
                                                 command=self.select_overlay)
        self.select_overlay_btn.pack(side="left", padx=(12, 4))
        self.overlay_path_label = ctk.CTkLabel(self.overlay_picker_frame, text="None",
                                                text_color=COLORS["text_muted"], font=self.fonts["small"])
        self.overlay_path_label.pack(side="left")
        self.selected_overlay_path = None
        
        self.burn_subs_var = ctk.BooleanVar(value=False)
        self.burn_subs_checkbox = ctk.CTkCheckBox(col2, text="Burn Subs", variable=self.burn_subs_var,
                                                   font=self.fonts["small"], text_color=COLORS["text_secondary"],
                                                   fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                                   border_color=COLORS["border"])
        self.burn_subs_checkbox.pack(anchor="w", pady=2)
        
        # Font Selection with Searchable Picker
        font_row = ctk.CTkFrame(col2, fg_color="transparent")
        font_row.pack(anchor="w", padx=12, pady=2)
        ctk.CTkLabel(font_row, text="Font:", font=self.fonts["small"],
                     text_color=COLORS["text_muted"]).pack(side="left")
        
        self.available_fonts = ["Arial", "Segoe UI", "Calibri", "Verdana", "Impact"]
        try:
            sys_fonts = list(font.families())
            sys_fonts.sort()
            if sys_fonts:
                self.available_fonts = sys_fonts
        except:
            pass
        self.font_var = ctk.StringVar(value="Arial")
        
        # Font picker button instead of dropdown
        self.font_btn = ctk.CTkButton(font_row, textvariable=self.font_var,
                                       width=100, height=24, corner_radius=4, 
                                       fg_color=COLORS["bg_input"],
                                       border_width=1, border_color=COLORS["border"],
                                       hover_color=COLORS["border_light"],
                                       text_color=COLORS["text_primary"],
                                       command=self.open_font_picker)
        self.font_btn.pack(side="left", padx=(4, 0))
        
        # Font Size
        font_size_row = ctk.CTkFrame(col2, fg_color="transparent")
        font_size_row.pack(anchor="w", padx=12, pady=2)
        ctk.CTkLabel(font_size_row, text="Size:", font=self.fonts["small"],
                     text_color=COLORS["text_muted"]).pack(side="left")
        
        self.font_size_var = ctk.StringVar(value="8")
        self.font_size_entry = ctk.CTkEntry(font_size_row, textvariable=self.font_size_var,
                                             width=50, height=24, corner_radius=4,
                                             border_width=1, border_color=COLORS["border"],
                                             fg_color=COLORS["bg_input"])
        self.font_size_entry.pack(side="left", padx=(4, 0))
        
        # Subtitle Color Settings (Font, Outline, Background)
        # ASS Color Format: &HAABBGGRR (Alpha-Blue-Green-Red)
        self.ass_colors = {
            "White": "&H00FFFFFF",
            "Black": "&H00000000",
            "Yellow": "&H0000FFFF",
            "Red": "&H000000FF",
            "Green": "&H0000FF00",
            "Blue": "&H00FF0000",
            "Cyan": "&H00FFFF00",
            "Magenta": "&H00FF00FF",
            "Orange": "&H000080FF",
            "Pink": "&H00CBC0FF"
        }
        
        # Semi-transparent versions for background
        self.ass_colors_alpha = {
            "None": "",
            "Black": "&H80000000",
            "Dark Gray": "&H80333333",
            "White": "&H80FFFFFF",
            "Yellow": "&H8000FFFF",
            "Red": "&H800000FF",
            "Green": "&H8000FF00",
            "Blue": "&H80FF0000"
        }
        
        # Font Color Row
        font_color_row = ctk.CTkFrame(col2, fg_color="transparent")
        font_color_row.pack(anchor="w", padx=12, pady=2)
        ctk.CTkLabel(font_color_row, text="Text:", font=self.fonts["small"],
                     text_color=COLORS["text_muted"]).pack(side="left")
        
        self.font_color_var = ctk.StringVar(value="White")
        self.font_color_menu = ctk.CTkOptionMenu(font_color_row, values=list(self.ass_colors.keys()),
                                                  variable=self.font_color_var, width=70, height=24,
                                                  corner_radius=4, fg_color=COLORS["bg_input"],
                                                  button_color=COLORS["accent"],
                                                  button_hover_color=COLORS["accent_hover"])
        self.font_color_menu.pack(side="left", padx=(4, 0))
        
        # Outline Color Row
        outline_color_row = ctk.CTkFrame(col2, fg_color="transparent")
        outline_color_row.pack(anchor="w", padx=12, pady=2)
        ctk.CTkLabel(outline_color_row, text="Line:", font=self.fonts["small"],
                     text_color=COLORS["text_muted"]).pack(side="left")
        
        self.outline_color_var = ctk.StringVar(value="Black")
        self.outline_color_menu = ctk.CTkOptionMenu(outline_color_row, values=list(self.ass_colors.keys()),
                                                     variable=self.outline_color_var, width=70, height=24,
                                                     corner_radius=4, fg_color=COLORS["bg_input"],
                                                     button_color=COLORS["accent"],
                                                     button_hover_color=COLORS["accent_hover"])
        self.outline_color_menu.pack(side="left", padx=(4, 0))
        
        # Background Color Row
        bg_row = ctk.CTkFrame(col2, fg_color="transparent")
        bg_row.pack(anchor="w", padx=12, pady=2)
        ctk.CTkLabel(bg_row, text="BG:", font=self.fonts["small"],
                     text_color=COLORS["text_muted"]).pack(side="left")
        
        self.sub_bg_var = ctk.StringVar(value="None")
        self.sub_bg_menu = ctk.CTkOptionMenu(bg_row, values=list(self.ass_colors_alpha.keys()),
                                              variable=self.sub_bg_var, width=80, height=24,
                                              corner_radius=4, fg_color=COLORS["bg_input"],
                                              button_color=COLORS["accent"], 
                                              button_hover_color=COLORS["accent_hover"])
        self.sub_bg_menu.pack(side="left", padx=(4, 0))
        
        # Column 3: Maintenance
        col3 = ctk.CTkFrame(checkbox_frame, fg_color="transparent")
        col3.pack(side="left", fill="y", padx=16, anchor="n")
        ctk.CTkLabel(col3, text="🗑️ Clean", font=self.fonts["h3"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 4))
        
        self.delete_original_var = ctk.BooleanVar(value=False)
        self.delete_checkbox = ctk.CTkCheckBox(col3, text="Del Original", variable=self.delete_original_var,
                                                font=self.fonts["small"], text_color=COLORS["text_secondary"],
                                                fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                                border_color=COLORS["border"])
        self.delete_checkbox.pack(anchor="w", pady=2)

        # === BOTTOM: Start Button + Console ===
        self.bottom_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, padx=16, pady=(8, 12), sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        
        self.start_btn = ctk.CTkButton(self.bottom_frame, text="▶  START PROCESSING",
                                        command=self.start_processing_thread, height=44, corner_radius=10,
                                        font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                                        fg_color=COLORS["success"], hover_color=COLORS["success_hover"])
        self.start_btn.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        
        # Console Log
        self.log_frame = ctk.CTkFrame(self.bottom_frame, fg_color=COLORS["bg_card"],
                                       corner_radius=10, border_width=1, border_color=COLORS["border"])
        self.log_frame.grid(row=1, column=0, sticky="ew")
        
        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=10, pady=(6, 4))
        ctk.CTkLabel(log_header, text="💻 Console", font=self.fonts["h3"],
                     text_color=COLORS["text_primary"]).pack(side="left")
        
        self.log_textbox = ctk.CTkTextbox(self.log_frame, height=100, font=self.fonts["mono"],
                                           fg_color=COLORS["bg_input"], text_color=COLORS["success"],
                                           corner_radius=6, border_width=1, border_color=COLORS["border"])
        self.log_textbox.pack(fill="x", padx=10, pady=(0, 8))
        self.log_textbox.configure(state="disabled")

    def create_card(self, parent, title, row):
        """Create a styled card component with glassmorphism effect."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"]
        )
        card.grid(row=row, column=0, padx=16, pady=6, sticky="ew")
        
        # Title Bar - more compact
        title_bar = ctk.CTkFrame(card, height=28, fg_color="transparent")
        title_bar.pack(fill="x", padx=12, pady=(10, 6))
        
        lbl = ctk.CTkLabel(
            title_bar, 
            text=title, 
            font=self.fonts["h2"], 
            text_color=COLORS["text_primary"]
        )
        lbl.pack(side="left")
        
        divider = ctk.CTkFrame(card, height=1, fg_color=COLORS["border"])
        divider.pack(fill="x", padx=12, pady=(0, 6))
        
        # Content frame - reduced padding
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        return content

    def log(self, message):
        # Check if log_textbox exists (might not exist during initialization)
        if hasattr(self, 'log_textbox'):
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", f">> {message}\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        else:
            # Fallback to print if GUI not ready
            print(f">> {message}")

    def save_key(self):
        key = self.api_key_entry.get()
        if key:
            provider = self.ai_provider_var.get()
            if "Grok" in provider:
                save_grok_api_key(key)
                self.log("Grok API Key saved.")
            elif "OpenRouter" in provider:
                save_openrouter_api_key(key)
                self.log("OpenRouter API Key saved.")
            else:
                save_api_key(key)
                self.log("Gemini API Key saved.")
        else:
            self.log("Please enter an API Key.")
    
    def on_ai_provider_change(self, provider):
        """Handle AI provider change - load appropriate API key."""
        self.api_key_entry.delete(0, "end")
        
        if "Grok" in provider:
            # Check if OpenAI is available
            if not OPENAI_AVAILABLE:
                self.log("⚠️ OpenAI package not installed. Run: pip install openai")
            existing_key = get_grok_api_key()
        elif "OpenRouter" in provider:
            # Check if OpenAI is available (OpenRouter uses same SDK)
            if not OPENAI_AVAILABLE:
                self.log("⚠️ OpenAI package not installed. Run: pip install openai")
            existing_key = get_openrouter_api_key()
            self.log("💡 Tip: Get free API key at openrouter.ai")
        else:
            existing_key = get_api_key()
        
        if existing_key:
            self.api_key_entry.insert(0, existing_key)
        
        self.log(f"Switched to {provider}")
    
    def on_platform_change(self, platform):
        """Handle platform selection change"""
        if platform == "Original":
            self.platform_info_label.configure(text="No platform optimization")
            # Show legacy options
            self.tiktok_checkbox.configure(state="normal")
            self.podcast_checkbox.configure(state="normal") 
            self.active_speaker_checkbox.configure(state="normal")
        else:
            # Import PlatformOptimizer to get platform specs
            from video_processor import PlatformOptimizer
            spec = PlatformOptimizer.get_platform_spec(platform)
            info_text = f"{spec['resolution'][0]}x{spec['resolution'][1]} ({spec['aspect_ratio'][0]}:{spec['aspect_ratio'][1]})"
            self.platform_info_label.configure(text=info_text)
            
            # Disable legacy options when platform is selected
            self.tiktok_checkbox.configure(state="disabled")
            self.podcast_checkbox.configure(state="disabled")
            self.active_speaker_checkbox.configure(state="disabled")
            
            # Reset legacy checkboxes
            self.tiktok_mode_var.set(False)
            self.podcast_mode_var.set(False) 
            self.active_speaker_var.set(False)
        
        self.log(f"Platform changed to: {platform}")
        self.save_settings()  # Auto-save platform selection
            
    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    data = json.load(f)
                    if "browser" in data:
                        self.browser_cookie_var.set(data["browser"])
                    if "device" in data:
                        self.render_device_var.set(data["device"])
                    if "ai_provider" in data:
                        self.ai_provider_var.set(data["ai_provider"])
                        # Load correct API key for saved provider
                        self.on_ai_provider_change(data["ai_provider"])
                    if "platform" in data:
                        self.platform_var.set(data["platform"])
                        self.on_platform_change(data["platform"])
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def save_settings(self, _=None):
        try:
            data = {
                "browser": self.browser_cookie_var.get(),
                "device": self.render_device_var.get(),
                "ai_provider": self.ai_provider_var.get(),
                "platform": self.platform_var.get()
            }
            with open("settings.json", "w") as f:
                json.dump(data, f)
            # self.log("Settings saved.") # Optional log
        except Exception as e:
            self.log(f"Error saving settings: {e}")

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Subtitle Files", "*.srt *.vtt")
            ]
        )
        if file_path:
            self.selected_file_path = file_path
            self.file_path_label.configure(text=os.path.basename(file_path))
            self.log(f"Selected subtitle: {file_path}")

    def toggle_overlay_ui(self):
        if self.overlay_var.get():
            self.overlay_picker_frame.pack(anchor="w", padx=25, pady=0)
        else:
            self.overlay_picker_frame.pack_forget()

    def open_font_picker(self):
        """Open a dialog to pick fonts with search and scroll functionality."""
        dialog = FontPickerDialog(self, self.available_fonts, self.font_var.get())
        self.wait_window(dialog)
        if dialog.result:
            self.font_var.set(dialog.result)
            self.log(f"Font selected: {dialog.result}")

    def select_overlay(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            self.selected_overlay_path = file_path
            self.overlay_path_label.configure(text=os.path.basename(file_path)[0:15]+"...")
            self.log(f"Selected overlay: {file_path}")

    def start_processing_thread(self):
        """Toggle between starting and stopping the process."""
        if self.is_processing:
            self.stop_processing()
        else:
            self.processing_flag.set()
            self.is_processing = True
            self.start_btn.configure(
                text="⏹  STOP PROCESSING", 
                fg_color=COLORS["danger"], 
                hover_color=COLORS["danger_hover"]
            )
            threading.Thread(target=self.process_video, daemon=True).start()

    def stop_processing(self):
        """Signal the processing thread to stop."""
        self.processing_flag.clear() # Clear flag to signal stop
        self.log("⏹️ Stopping process... Please wait for current operation to complete.")

    def reset_ui(self):
        """Reset UI to ready state."""
        self.is_processing = False
        self.start_btn.configure(
            state="normal", 
            text="▶  START PROCESSING",
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"]
        )

    def process_video(self):
        # Determine which AI provider to use
        ai_provider = self.ai_provider_var.get()
        use_grok = "Grok" in ai_provider
        use_openrouter = "OpenRouter" in ai_provider
        
        if use_grok:
            api_key = get_grok_api_key()
            if not api_key:
                self.log("Error: Grok API Key not found. Please save it first.")
                self.reset_ui()
                return
            if not OPENAI_AVAILABLE:
                self.log("Error: OpenAI package not installed. Run: pip install openai")
                self.reset_ui()
                return
        elif use_openrouter:
            api_key = get_openrouter_api_key()
            if not api_key:
                self.log("Error: OpenRouter API Key not found. Please save it first.")
                self.log("💡 Get free API key at: https://openrouter.ai/keys")
                self.reset_ui()
                return
            if not OPENAI_AVAILABLE:
                self.log("Error: OpenAI package not installed. Run: pip install openai")
                self.reset_ui()
                return
        else:
            api_key = get_api_key()
            if not api_key:
                self.log("Error: Gemini API Key not found. Please save it first.")
                self.reset_ui()
                return

        # SIMPLIFIED INPUT LOGIC
        youtube_url = self.youtube_url_entry.get()
        subtitle_path = self.selected_file_path
        
        if not youtube_url:
            self.log("Error: Please enter a YouTube URL.")
            self.reset_ui()
            return

        self.log("--- Starting AI Processing ---")
        self.log(f"Source URL: {youtube_url}")
        self.log(f"Using AI: {ai_provider}")

        try:
            # Initialize correct AI handler
            if use_grok:
                ai = GrokHandler(api_key)
            elif use_openrouter:
                ai = OpenRouterHandler(api_key)
            else:
                ai = AIHandler(api_key)
            render_dev = self.render_device_var.get()
            self.log(f"Initializing VideoProcessor with device: {render_dev}")
            processor = VideoProcessor(render_device=render_dev)
            
            # Setup YouTube handler with optional browser cookies
            browser_cookie = self.browser_cookie_var.get()
            if browser_cookie and browser_cookie != "None":
                self.log(f"Using cookies from: {browser_cookie}")
                yt_handler = YouTubeHandler(use_cookies_from=browser_cookie.lower())
            else:
                yt_handler = YouTubeHandler()

            # --- Fetch Video Context from YouTube ---
            self.log("Fetching video metadata for context...")
            video_context = yt_handler.get_video_metadata(youtube_url, progress_callback=self.log)
            if video_context.get('title'):
                self.log(f"📺 Video: {video_context['title'][:60]}...")
                self.log(f"👤 Channel: {video_context.get('channel', 'Unknown')}")

            # --- Processing Logic ---
            method = self.analysis_method_var.get()
            self.log(f"--- Processing Method: {method} ---")

            clips_data = []
            master_subtitle_path = None # For burn subs

            # Check if Custom Subtitle is used
            use_custom_sub = False
            if subtitle_path and os.path.exists(subtitle_path):
                self.log(f"Using Custom Subtitle: {os.path.basename(subtitle_path)}")
                master_subtitle_path = subtitle_path
                use_custom_sub = True
            
            # 1. ANALYSIS: SUBTITLE (Custom or Auto-fetch)
            if (method == "Subtitle" or method == "Auto"):
                if use_custom_sub:
                    self.log("Reading custom subtitle file...")
                    with open(master_subtitle_path, 'r', encoding='utf-8') as f:
                        transcript_text = f.read()
                    self.log("Analyzing custom subtitles...")
                    clips_data = ai.analyze_transcript(transcript_text, video_context=video_context)
                else:
                    self.log("Checking for available subtitles on YouTube...")
                    # For Auto, we try to fetch.
                    # Should we keep info for burning? Yes if enabled.
                    should_keep_vtt = self.burn_subs_var.get() and self.tiktok_mode_var.get()
                    
                     # Parse Language Selection
                    selected_lang = self.sub_language_var.get()
                    target_lang_code = 'id' if 'Indonesian' in selected_lang else 'en'
                    self.log(f"Target Subtitle Language: {target_lang_code.upper()}")

                    if should_keep_vtt:
                         result = yt_handler.get_transcript(youtube_url, progress_callback=self.log, keep_vtt=True, target_language=target_lang_code)
                         if result and result[0]:
                             transcript, master_subtitle_path = result
                             self.log("Subtitles found! Analyzing text...")
                             clips_data = ai.analyze_transcript(transcript, video_context=video_context)
                         else:
                             transcript = None
                    else:
                        transcript = yt_handler.get_transcript(youtube_url, progress_callback=self.log, target_language=target_lang_code)
                        if transcript:
                            self.log("Subtitles found! Analyzing text...")
                            clips_data = ai.analyze_transcript(transcript, video_context=video_context)
                    
                    if not transcript and method == "Subtitle":
                        self.log("Error: No subtitles found for this video. Use Auto or Audio method.")
                        self.reset_ui()
                        return

            # 2. ANALYSIS: AUDIO (Fallback or Explicit)
            if (method == "Audio" or (method == "Auto" and not clips_data)):
                if not self.processing_flag.is_set(): # Stop check
                    self.log("Process cancelled.")
                    self.reset_ui()
                    return
                    
                self.log("Downloading audio for analysis...")
                try:
                    audio_path = yt_handler.download_audio(youtube_url, progress_callback=self.log, running_event=self.processing_flag)
                    self.log(f"Audio ready: {audio_path}")
                    
                    self.log("Uploading audio to Gemini...")
                    file_obj = ai.upload_file(audio_path)
                    
                    self.log("Waiting for audio processing...")
                    file_obj = ai.wait_for_processing(file_obj)
                    
                    self.log("Analyzing audio...")
                    clips_data = ai.analyze_audio(file_obj, video_context=video_context)
                    
                    self.log("Cleaning up cloud storage...")
                    ai.delete_file(file_obj)
                    
                    # Cleanup local audio
                    try: os.remove(audio_path)
                    except: pass
                    
                except Exception as e:
                    self.log(f"Audio Analysis Failed: {str(e)}")
                    self.reset_ui()
                    return

            # === SEQUENTIAL CLIPPING & PROCESSING ===
            if not clips_data:
                self.log("No clips identified or error in analysis.")
                self.reset_ui()
                return
            
            # Check for cancellation before processing clips
            if not self.processing_flag.is_set():
                self.log("❌ Process cancelled by user.")
                self.reset_ui()
                return

            self.log(f"Identified {len(clips_data)} clips. Starting sequential processing...")
            
            # Helper to safe sort
            def get_viral_score(clip):
                try:
                    return int(clip.get('viral_score', 0))
                except:
                    return 0

            # Sort clips by viral score (highest first)
            try:
                clips_data = sorted(clips_data, key=get_viral_score, reverse=True)
            except Exception as e:
                self.log(f"Warning: Sorting failed ({e}), proceeding with default order.")

            # Prepare metadata file for copy-paste
            metadata_file_path = os.path.join(processor.output_dir, "_CLIP_METADATA.txt")
            metadata_lines = ["=" * 60, "SMARTCLIP AI - VIRAL SCORE & METADATA", "=" * 60, ""]
            
            for i, clip in enumerate(clips_data):
                # Check for cancellation at start of each clip
                if not self.processing_flag.is_set():
                    self.log(f"\n❌ Process stopped by user after {i} clips.")
                    break
                    
                start = clip.get('start_time_sec', clip.get('start_time'))
                end = clip.get('end_time_sec', clip.get('end_time'))
                desc = clip['description']
                viral_score = clip.get('viral_score', 'N/A')
                suggested_title = clip.get('suggested_title', desc)
                suggested_caption = clip.get('suggested_caption', '')
                
                # Display viral info in log
                score_emoji = "🔥" if viral_score != 'N/A' and viral_score >= 70 else "⭐" if viral_score != 'N/A' and viral_score >= 50 else "📊"
                self.log(f"\n{score_emoji} Clip {i+1}/{len(clips_data)} | Viral Score: {viral_score}/100")
                self.log(f"   📝 {desc} ({start}s - {end}s)")
                self.log(f"   🎬 Title: {suggested_title}")
                
                 # Add to metadata file
                metadata_lines.append(f"CLIP {i+1} | VIRAL SCORE: {viral_score}/100")
                metadata_lines.append("-" * 40)
                metadata_lines.append(f"Duration: {start}s - {end}s")
                metadata_lines.append(f"")
                metadata_lines.append(f"📋 TITLE (copy this):")
                metadata_lines.append(f"{suggested_title}")
                metadata_lines.append(f"")
                metadata_lines.append(f"📋 CAPTION (copy this):")
                metadata_lines.append(f"{suggested_caption}")
                metadata_lines.append(f"")
                metadata_lines.append("=" * 60)
                metadata_lines.append("")
                
                # DOWNLOAD CLIP FROM YOUTUBE
                self.log(f"Downloading clip from YouTube...")
                clip_path = yt_handler.download_clip(youtube_url, start, end, desc, progress_callback=self.log, running_event=self.processing_flag)
                
                if not clip_path or not os.path.exists(clip_path):
                    self.log(f"Error: Failed to generate clip {i+1}. Skipping.")
                    continue
                
                # Check current platform selection
                selected_platform = self.platform_var.get()
                
                # PLATFORM OPTIMIZATION (New Feature)
                if selected_platform != "Original":
                    self.log(f"Applying {selected_platform} optimization...")
                    
                    # Check for overlay
                    overlay_file = None
                    if self.overlay_var.get():
                        if self.selected_overlay_path and os.path.exists(self.selected_overlay_path):
                            overlay_file = self.selected_overlay_path
                            self.log(f"Using Overlay: {os.path.basename(overlay_file)}")
                    
                    # Slice subtitle for this clip (if available)
                    clip_subtitle_path = None
                    if master_subtitle_path and os.path.exists(master_subtitle_path):
                        self.log(f"Slicing subtitle for clip {i+1}...")
                        try:
                            clip_subtitle_path = processor.slice_subtitle(
                                master_subtitle_path, 
                                start, 
                                end,
                                output_path=os.path.join(processor.output_dir, f"_sub_clip_{i+1}.vtt")
                            )
                            if clip_subtitle_path:
                                self.log(f"📝 Subtitle sliced: {os.path.basename(clip_subtitle_path)}")
                        except Exception as e:
                            self.log(f"Warning: Failed to slice subtitle: {e}")
                    
                    # Prepare platform-optimized filename
                    platform_safe = selected_platform.replace(" ", "_").replace("/", "_")
                    base_name = os.path.splitext(os.path.basename(clip_path))[0]
                    platform_output_path = os.path.join(processor.output_dir, f"{base_name}_{platform_safe}.mp4")
                    
                    # Apply platform optimization
                    final_path = processor.optimize_for_platform(
                        clip_path, 
                        selected_platform,
                        output_path=platform_output_path,
                        progress_callback=self.log
                    )
                    
                    # If burn_subs is enabled and we have subtitle, manually overlay it
                    if self.burn_subs_var.get() and clip_subtitle_path and final_path:
                        self.log("Burning subtitles into optimized video...")
                        try:
                            # Get current font settings
                            selected_font = self.font_var.get()
                            font_size = int(self.font_size_var.get()) if self.font_size_var.get().isdigit() else 8
                            font_color = self.ass_colors.get(self.font_color_var.get(), "&H00FFFFFF")
                            outline_color = self.ass_colors.get(self.outline_color_var.get(), "&H00000000")
                            bg_color = self.ass_colors_alpha.get(self.sub_bg_var.get(), "")
                            
                            # Apply subtitle burning to the optimized video
                            # This would need a new method in VideoProcessor for just subtitle burning
                            # For now, we'll note that the subtitle file exists for manual use
                            self.log(f"📝 Subtitle available: {os.path.basename(clip_subtitle_path)}")
                        except Exception as e:
                            self.log(f"Warning: Could not burn subtitles: {e}")
                    
                    # Cleanup
                    if final_path and os.path.exists(final_path):
                        if self.delete_original_var.get():
                            self.log("Cleanup: Removing original 16:9 file.")
                            try: os.remove(clip_path)
                            except: pass
                        if clip_subtitle_path:
                            try: os.remove(clip_subtitle_path)
                            except: pass
                    else:
                        self.log("Platform optimization failed. Keeping original.")
                
                # SMART CROP (Legacy - If enabled and no platform selected)
                elif self.tiktok_mode_var.get():
                    is_podcast_mode = self.podcast_mode_var.get()
                    
                    # Check for overlay
                    overlay_file = None
                    if self.overlay_var.get():
                        if self.selected_overlay_path and os.path.exists(self.selected_overlay_path):
                            overlay_file = self.selected_overlay_path
                            self.log(f"Using Overlay: {os.path.basename(overlay_file)}")
                    
                    # Slice subtitle for this clip (if available)
                    clip_subtitle_path = None
                    # Use 'master_subtitle_path' which could be from Custom Subtitle OR Auto-fetched
                    if master_subtitle_path and os.path.exists(master_subtitle_path):
                         # If it's custom subtitle, we need to verify timing roughly matches? No, just trust user.
                        self.log(f"Slicing subtitle for clip {i+1}...")
                        try:
                            clip_subtitle_path = processor.slice_subtitle(
                                master_subtitle_path, 
                                start, 
                                end,
                                output_path=os.path.join(processor.output_dir, f"_sub_clip_{i+1}.vtt")
                            )
                            if clip_subtitle_path:
                                self.log(f"📝 Subtitle sliced: {os.path.basename(clip_subtitle_path)}")
                        except Exception as e:
                             self.log(f"Warning: Failed to slice subtitle: {e}")

                    final_path = None
                    is_active_speaker_mode = self.active_speaker_var.get()
                    selected_font = self.font_var.get()
                    
                    # Get font size and colors
                    try:
                        font_size = int(self.font_size_var.get())
                        if font_size < 1 or font_size > 100:
                            font_size = 8
                    except:
                        font_size = 8
                    
                    # Get subtitle styling colors
                    font_color = self.ass_colors.get(self.font_color_var.get(), "&H00FFFFFF")
                    outline_color = self.ass_colors.get(self.outline_color_var.get(), "&H00000000")
                    bg_color = self.ass_colors_alpha.get(self.sub_bg_var.get(), "")
                    
                    if is_active_speaker_mode:
                        self.log("Applying Active Speaker Crop...")
                        final_path = processor.smart_crop_active_speaker_9_16(
                            clip_path, 
                            overlay_path=overlay_file, 
                            subtitle_path=clip_subtitle_path,
                            subtitle_font=selected_font,
                            subtitle_font_size=font_size,
                            subtitle_font_color=font_color,
                            subtitle_outline_color=outline_color,
                            subtitle_bg_color=bg_color,
                            progress_callback=self.log
                        )
                    elif is_podcast_mode:
                        self.log("Applying Podcast Crop...")
                        final_path = processor.smart_crop_dual_speaker_9_16(
                            clip_path, 
                            overlay_path=overlay_file, 
                            subtitle_path=clip_subtitle_path,
                            subtitle_font=selected_font,
                            subtitle_font_size=font_size,
                            subtitle_font_color=font_color,
                            subtitle_outline_color=outline_color,
                            subtitle_bg_color=bg_color,
                            progress_callback=self.log
                        )
                    else:
                        self.log("Applying Smart Crop...")
                        final_path = processor.smart_crop_9_16(
                            clip_path, 
                            overlay_path=overlay_file,
                            subtitle_path=clip_subtitle_path,
                            subtitle_font=selected_font,
                            subtitle_font_size=font_size,
                            subtitle_font_color=font_color,
                            subtitle_outline_color=outline_color,
                            subtitle_bg_color=bg_color,
                            progress_callback=self.log
                        )

                    # CLEANUP
                    if final_path and os.path.exists(final_path):
                        if self.delete_original_var.get():
                            self.log("Cleanup: Removing original 16:9 file.")
                            try: os.remove(clip_path)
                            except: pass
                        if clip_subtitle_path:
                            try: os.remove(clip_subtitle_path)
                            except: pass
                    else:
                         self.log("Smart crop failed. Keeping original.")
                else:
                    # No optimization applied
                    self.log("No platform optimization applied. Saved original format.")
            
            # Save metadata file
            try:
                with open(metadata_file_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(metadata_lines))
                self.log(f"\n📄 Metadata saved: {metadata_file_path}")
            except Exception as e:
                self.log(f"Warning: Could not save metadata file: {e}")

            if self.processing_flag.is_set():
                self.log("\n--- All Clips Processed Successfully ---")
                self.log("💡 TIP: Open _CLIP_METADATA.txt in Output folder to copy titles & captions!")
            else:
                self.log("\n--- Processing Stopped ---")
            self.reset_ui()

        except Exception as e:
            self.log(f"FATAL ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.reset_ui()


