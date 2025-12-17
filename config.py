import os
from dotenv import load_dotenv, set_key

# Load environment variables from .env file
load_dotenv()

ENV_FILE = ".env"

def get_api_key():
    """Retrieve the Gemini API Key from environment variables."""
    return os.getenv("GEMINI_API_KEY")

def save_api_key(api_key):
    """Save the Gemini API Key to the .env file."""
    # Create .env if it doesn't exist
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w") as f:
            f.write("")
    
    set_key(ENV_FILE, "GEMINI_API_KEY", api_key)
    os.environ["GEMINI_API_KEY"] = api_key

def get_grok_api_key():
    """Retrieve the Grok (xAI) API Key from environment variables."""
    return os.getenv("GROK_API_KEY")

def save_grok_api_key(api_key):
    """Save the Grok (xAI) API Key to the .env file."""
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w") as f:
            f.write("")
    
    set_key(ENV_FILE, "GROK_API_KEY", api_key)
    os.environ["GROK_API_KEY"] = api_key

def get_openrouter_api_key():
    """Retrieve the OpenRouter API Key from environment variables."""
    return os.getenv("OPENROUTER_API_KEY")

def save_openrouter_api_key(api_key):
    """Save the OpenRouter API Key to the .env file."""
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w") as f:
            f.write("")
    
    set_key(ENV_FILE, "OPENROUTER_API_KEY", api_key)
    os.environ["OPENROUTER_API_KEY"] = api_key

def get_ffmpeg_path():
    """Retrieve the FFmpeg Path from environment variables."""
    return os.getenv("FFMPEG_PATH", r"C:\ffmpeg\bin")

def save_ffmpeg_path(ffmpeg_path):
    """Save the FFmpeg Path to the .env file."""
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w") as f:
            f.write("")
    
    set_key(ENV_FILE, "FFMPEG_PATH", ffmpeg_path)
    os.environ["FFMPEG_PATH"] = ffmpeg_path

# --- License Key Functions ---

def get_license_key():
    """Retrieve the license key from environment variables."""
    return os.getenv("SMARTCLIP_LICENSE_KEY")

def save_license_key(license_key):
    """Save the license key to the .env file."""
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w") as f:
            f.write("")
    
    set_key(ENV_FILE, "SMARTCLIP_LICENSE_KEY", license_key)
    os.environ["SMARTCLIP_LICENSE_KEY"] = license_key
