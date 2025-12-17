# SmartClip AI - License Handler
# Online license validation with Supabase

import os
import json
import hashlib
import uuid
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Tuple
import customtkinter as ctk

# --- Configuration ---
SUPABASE_URL = "https://hsvcrrxonhirwijwlald.supabase.co" 
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhzdmNycnhvbmhpcndpandsYWxkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyODgzNDksImV4cCI6MjA4MDg2NDM0OX0.YoF1X3o3PcoqLe0iqa998LrUPnUsChAjH5iyeH1k8v4"  # Will be replaced by user

# Trial settings
TRIAL_HOURS = 6
TRIAL_FILE = ".smartclip_trial"

# Offline grace period
OFFLINE_GRACE_DAYS = 3
CACHE_FILE = ".smartclip_license_cache"


def get_hardware_id() -> str:
    """Generate a unique hardware ID based on machine characteristics."""
    try:
        # Get MAC address
        mac = hex(uuid.getnode())[2:]
        
        # Get machine name
        import platform
        machine_info = f"{platform.node()}-{platform.processor()[:20]}"
        
        # Create hash
        combined = f"{mac}-{machine_info}"
        hardware_id = hashlib.sha256(combined.encode()).hexdigest()[:32]
        return hardware_id
    except Exception:
        # Fallback to random UUID if we can't get hardware info
        return str(uuid.uuid4()).replace("-", "")[:32]


def get_trial_info() -> Tuple[bool, Optional[datetime], float]:
    """
    Check trial status with anti-rollback protection.
    Returns: (is_trial_active, trial_end_time, hours_remaining)
    """
    try:
        if os.path.exists(TRIAL_FILE):
            with open(TRIAL_FILE, "r") as f:
                data = json.load(f)
                trial_start = datetime.fromisoformat(data.get("start_time"))
                trial_end = trial_start + timedelta(hours=TRIAL_HOURS)
                last_seen = datetime.fromisoformat(data.get("last_seen", data.get("start_time")))
                usage_count = data.get("usage_count", 0)
                
                now = datetime.now()
                
                # Anti-rollback check: if current time is before last_seen, user likely changed clock
                if now < last_seen - timedelta(minutes=5):  # 5 min tolerance for timezone issues
                    # Time manipulation detected! Invalidate trial immediately
                    _mark_trial_tampered()
                    return False, None, 0
                
                # Check if trial was tampered
                if data.get("tampered", False):
                    return False, None, 0
                
                # Update last_seen and usage_count
                _update_trial_usage(data)
                
                if now < trial_end:
                    remaining = (trial_end - now).total_seconds() / 3600
                    return True, trial_end, remaining
                else:
                    return False, trial_end, 0
        else:
            # First run - start trial
            start_trial()
            return get_trial_info()
    except Exception:
        return False, None, 0


def _mark_trial_tampered():
    """Mark trial as tampered (cannot be undone without deleting file)."""
    try:
        if os.path.exists(TRIAL_FILE):
            with open(TRIAL_FILE, "r") as f:
                data = json.load(f)
            data["tampered"] = True
            data["tampered_at"] = datetime.now().isoformat()
            with open(TRIAL_FILE, "w") as f:
                json.dump(data, f)
    except Exception:
        pass


def _update_trial_usage(data: dict):
    """Update last_seen timestamp and usage count."""
    try:
        data["last_seen"] = datetime.now().isoformat()
        data["usage_count"] = data.get("usage_count", 0) + 1
        with open(TRIAL_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def start_trial():
    """Initialize trial period."""
    try:
        data = {
            "start_time": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "hardware_id": get_hardware_id(),
            "usage_count": 1,
            "tampered": False
        }
        with open(TRIAL_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def is_trial_valid() -> Tuple[bool, float]:
    """
    Check if trial is still valid.
    Returns: (is_valid, hours_remaining)
    """
    is_active, _, hours_remaining = get_trial_info()
    return is_active, hours_remaining


def validate_license_online(license_key: str) -> Tuple[bool, str]:
    """
    Validate license key against Supabase.
    Returns: (is_valid, message)
    """
    if not SUPABASE_URL or SUPABASE_URL == "YOUR_SUPABASE_URL":
        return False, "Supabase not configured. Please setup SUPABASE_URL and SUPABASE_ANON_KEY in license_handler.py"
    
    try:
        hardware_id = get_hardware_id()
        
        # Query Supabase for the license
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        
        # Check if license exists
        url = f"{SUPABASE_URL}/rest/v1/licenses?license_key=eq.{license_key}&select=*"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return False, f"Server error: {response.status_code}"
        
        licenses = response.json()
        
        if not licenses:
            return False, "License key tidak ditemukan."
        
        license_data = licenses[0]
        
        # Check if license is active
        if not license_data.get("is_active", False):
            return False, "License telah dinonaktifkan."
        
        # Check expiry
        expires_at = license_data.get("expires_at")
        if expires_at:
            expiry_date = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if datetime.now(expiry_date.tzinfo) > expiry_date:
                return False, f"License sudah expired pada {expiry_date.strftime('%Y-%m-%d')}."
        
        # Check hardware binding
        bound_hardware = license_data.get("hardware_id")
        if bound_hardware:
            if bound_hardware != hardware_id:
                return False, "License sudah terdaftar di perangkat lain."
        else:
            # First activation - bind to this hardware
            update_url = f"{SUPABASE_URL}/rest/v1/licenses?id=eq.{license_data['id']}"
            update_data = {"hardware_id": hardware_id}
            requests.patch(update_url, headers=headers, json=update_data, timeout=10)
        
        # Cache the successful validation
        cache_license(license_key, license_data)
        
        return True, "License valid! ✅"
        
    except requests.exceptions.ConnectionError:
        # No internet - check offline cache
        return check_offline_cache(license_key)
    except requests.exceptions.Timeout:
        return check_offline_cache(license_key)
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def cache_license(license_key: str, license_data: dict):
    """Cache license data for offline use."""
    try:
        cache_data = {
            "license_key": license_key,
            "validated_at": datetime.now().isoformat(),
            "expires_at": license_data.get("expires_at"),
            "hardware_id": get_hardware_id()
        }
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f)
    except Exception:
        pass


def check_offline_cache(license_key: str) -> Tuple[bool, str]:
    """Check if we have a valid cached license for offline use."""
    try:
        if not os.path.exists(CACHE_FILE):
            return False, "Tidak ada koneksi internet dan tidak ada cache license."
        
        with open(CACHE_FILE, "r") as f:
            cache_data = json.load(f)
        
        # Check if this is the same license key
        if cache_data.get("license_key") != license_key:
            return False, "License key tidak cocok dengan cache."
        
        # Check hardware ID
        if cache_data.get("hardware_id") != get_hardware_id():
            return False, "Hardware ID tidak cocok."
        
        # Check if within grace period
        validated_at = datetime.fromisoformat(cache_data.get("validated_at"))
        grace_end = validated_at + timedelta(days=OFFLINE_GRACE_DAYS)
        
        if datetime.now() > grace_end:
            return False, f"Offline grace period ({OFFLINE_GRACE_DAYS} hari) sudah habis. Hubungkan ke internet untuk validasi."
        
        remaining_days = (grace_end - datetime.now()).days
        return True, f"Offline mode aktif ({remaining_days} hari tersisa)"
        
    except Exception as e:
        return False, f"Cache error: {str(e)}"


class LicenseDialog(ctk.CTkToplevel):
    """Dialog for license key input."""
    
    def __init__(self, parent, trial_hours_remaining: float = 0):
        super().__init__(parent)
        
        self.title("SmartClip AI - Aktivasi License")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Result
        self.result = False
        self.license_key = None
        
        # Build UI
        self._build_ui(trial_hours_remaining)
        
        # Handle close button
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _build_ui(self, trial_hours_remaining: float):
        # Header
        header = ctk.CTkLabel(
            self, 
            text="🔐 SmartClip AI", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=(30, 10))
        
        # Trial info
        if trial_hours_remaining > 0:
            trial_text = f"⏱️ Trial tersisa: {trial_hours_remaining:.1f} jam"
            trial_color = "#2CC985"
        else:
            trial_text = "⚠️ Trial period sudah habis"
            trial_color = "#E74C3C"
        
        trial_label = ctk.CTkLabel(
            self,
            text=trial_text,
            font=ctk.CTkFont(size=14),
            text_color=trial_color
        )
        trial_label.pack(pady=(0, 20))
        
        # Info Frame
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(pady=10)

        ctk.CTkLabel(
            info_frame,
            text="Masukkan license key untuk mengaktifkan aplikasi.\nBeli license di:",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack()

        link_label = ctk.CTkLabel(
            info_frame,
            text="https://lynk.id/mrizkiiy",
            font=ctk.CTkFont(size=12, underline=True),
            text_color="#2CC985",
            cursor="hand2"
        )
        link_label.pack()
        
        # Make link clickable
        import webbrowser
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://lynk.id/mrizkiiy"))
        
        # License Key Entry
        self.key_entry = ctk.CTkEntry(
            self,
            placeholder_text="SMART-XXXX-XXXX-XXXX",
            width=350,
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.key_entry.pack(pady=20)
        
        # Status Label
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # Buttons Frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        # Activate Button
        self.activate_btn = ctk.CTkButton(
            btn_frame,
            text="✅ Aktivasi License",
            command=self._on_activate,
            width=150,
            height=40,
            fg_color="#2CC985",
            hover_color="#229965"
        )
        self.activate_btn.pack(side="left", padx=10)
        
        # Continue Trial Button (if trial still valid)
        if trial_hours_remaining > 0:
            self.trial_btn = ctk.CTkButton(
                btn_frame,
                text="⏱️ Lanjut Trial",
                command=self._on_continue_trial,
                width=150,
                height=40,
                fg_color="#3498DB",
                hover_color="#2980B9"
            )
            self.trial_btn.pack(side="left", padx=10)
        
        # Exit Button
        self.exit_btn = ctk.CTkButton(
            btn_frame,
            text="❌ Keluar",
            command=self._on_cancel,
            width=100,
            height=40,
            fg_color="#7F8C8D",
            hover_color="#5D6D7E"
        )
        self.exit_btn.pack(side="left", padx=10)
    
    def _on_activate(self):
        license_key = self.key_entry.get().strip()
        
        if not license_key:
            self.status_label.configure(text="❌ Masukkan license key!", text_color="#E74C3C")
            return
        
        self.status_label.configure(text="⏳ Memvalidasi...", text_color="gray")
        self.update()
        
        is_valid, message = validate_license_online(license_key)
        
        if is_valid:
            self.status_label.configure(text=f"✅ {message}", text_color="#2CC985")
            self.result = True
            self.license_key = license_key
            self.after(1000, self.destroy)
        else:
            self.status_label.configure(text=f"❌ {message}", text_color="#E74C3C")
    
    def _on_continue_trial(self):
        self.result = True
        self.license_key = "__TRIAL__"
        self.destroy()
    
    def _on_cancel(self):
        self.result = False
        self.destroy()


def check_license(parent_window) -> Tuple[bool, str]:
    """
    Main function to check license status.
    Shows dialog if needed.
    Returns: (is_licensed, license_type)  where license_type is "trial", "licensed", or "invalid"
    """
    from config import get_license_key, save_license_key
    
    # Check for saved license first
    saved_key = get_license_key()
    if saved_key:
        is_valid, message = validate_license_online(saved_key)
        if is_valid:
            return True, "licensed"
    
    # Check trial status
    is_trial_active, hours_remaining = is_trial_valid()
    
    # Show license dialog
    dialog = LicenseDialog(parent_window, hours_remaining if is_trial_active else 0)
    parent_window.wait_window(dialog)
    
    if dialog.result:
        if dialog.license_key == "__TRIAL__":
            return True, "trial"
        else:
            # Save the validated license
            save_license_key(dialog.license_key)
            return True, "licensed"
    
    return False, "invalid"
