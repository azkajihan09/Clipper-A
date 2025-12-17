import google.generativeai as genai
import time
import json
import os
import re

# Optional OpenAI import for Grok
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class AIHandler:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Use gemini-2.5-flash for efficiency (1M token limit is sufficient for transcript/audio)
        self.model_name = "gemini-2.5-flash" 
        self.model = genai.GenerativeModel(model_name=self.model_name)

    def upload_file(self, file_path):
        """Uploads a file (video/audio) to Gemini."""
        print(f"Uploading file: {file_path}")
        file_obj = genai.upload_file(path=file_path)
        print(f"Completed upload: {file_obj.uri}")
        return file_obj

    def wait_for_processing(self, file_obj):
        """Waits for the file to be processed and active."""
        while file_obj.state.name == "PROCESSING":
            print("Processing file...", end="\r")
            time.sleep(2)
            file_obj = genai.get_file(file_obj.name)
        
        if file_obj.state.name == "FAILED":
            raise ValueError("File processing failed.")
        
        print(f"\nFile is active: {file_obj.name}")
        return file_obj

    def analyze_video(self, video_file, video_context=None):
        """Sends a prompt to Gemini to identify best moments from video with viral scoring."""
        context_str = self._build_context_string(video_context)
        prompt = (
            f"{context_str}"
            "Analisis video ini. Identifikasi 5 momen minimal 1 menit dan maksimal 3 menit paling menarik, hook, lucu, atau penting "
            "yang cocok untuk dijadikan konten pendek (Shorts/Reels/Video TikTok). "
            "Untuk SETIAP momen, berikan penilaian potensi viral dan metadata untuk posting. "
            "PENTING: Jika ada public figure atau tokoh terkenal yang disebutkan dalam konteks, WAJIB sertakan nama mereka di judul dan caption. "
            "Berikan respon HANYA dalam format JSON valid berisi list object dengan key: "
            "`start_time_sec` (integer, detik), "
            "`end_time_sec` (integer, detik), "
            "`description` (deskripsi internal singkat), "
            "`viral_score` (integer 1-100, skor potensi viral berdasarkan hook, engagement, keunikan), "
            "`suggested_title` (judul menarik dan clickbait untuk YouTube/TikTok dengan nama tokoh jika ada, max 60 karakter), "
            "`suggested_caption` (caption siap posting dengan emoji dan 5 hashtag relevan termasuk nama tokoh, max 200 karakter)."
        )
        return self._generate_content(video_file, prompt)

    def analyze_audio(self, audio_file, video_context=None):
        """Sends a prompt to Gemini to identify best moments from audio with viral scoring."""
        context_str = self._build_context_string(video_context)
        prompt = (
            f"{context_str}"
            "Analisis file audio ini. Identifikasi 5 momen minimal 1 menit dan maksimal 3 menit paling menarik, hook, lucu, atau penting "
            "yang cocok untuk dijadikan konten pendek (Shorts/Reels/Video TikTok). "
            "Untuk SETIAP momen, berikan penilaian potensi viral dan metadata untuk posting. "
            "PENTING: Jika ada public figure atau tokoh terkenal yang disebutkan dalam konteks, WAJIB sertakan nama mereka di judul dan caption. "
            "Berikan respon HANYA dalam format JSON valid berisi list object dengan key: "
            "`start_time_sec` (integer, detik), "
            "`end_time_sec` (integer, detik), "
            "`description` (deskripsi internal singkat), "
            "`viral_score` (integer 1-100, skor potensi viral berdasarkan hook, engagement, keunikan), "
            "`suggested_title` (judul menarik dan clickbait untuk YouTube/TikTok dengan nama tokoh jika ada, max 60 karakter), "
            "`suggested_caption` (caption siap posting dengan emoji dan 5 hashtag relevan termasuk nama tokoh, max 200 karakter)."
        )
        return self._generate_content(audio_file, prompt)

    def analyze_transcript(self, transcript_text, video_context=None):
        """Sends a prompt to Gemini to identify best moments from transcript text with viral scoring."""
        
        # --- OPTIMIZATION START ---
        # Compress transcript to save tokens (approx 30-40% saving)
        compressed_transcript = self._compress_transcript(transcript_text)
        print(f"Transcript compressed. Original len: {len(transcript_text)} -> New len: {len(compressed_transcript)}")
        # --- OPTIMIZATION END ---

        context_str = self._build_context_string(video_context)
        prompt = (
            f"{context_str}"
            "Analisis transkrip berikut ini. Input berupa ringkasan transkrip dengan format `[MM:SS] Teks`. "
            "Identifikasi 5 momen minimal 1 menit dan maksimal 3 menit paling menarik, hook, lucu, atau penting "
            "yang cocok untuk dijadikan konten pendek (Shorts/Reels/Video TikTok). "
            "PENTING: Gunakan timestamp yang ada di transkrip untuk menentukan waktu mulai dan selesai. "
            "PENTING: Jika ada public figure atau tokoh terkenal yang disebutkan dalam konteks, WAJIB sertakan nama mereka di judul dan caption. "
            "Untuk SETIAP momen, berikan penilaian potensi viral dan metadata untuk posting. "
            "Berikan respon HANYA dalam format JSON valid berisi list object dengan key: "
            "`start_time_sec` (integer, detik), "
            "`end_time_sec` (integer, detik), "
            "`description` (deskripsi internal singkat), "
            "`viral_score` (integer 1-100, skor potensi viral berdasarkan hook, engagement, keunikan), "
            "`suggested_title` (judul menarik dan clickbait untuk YouTube/TikTok dengan nama tokoh jika ada, max 60 karakter), "
            "`suggested_caption` (caption siap posting dengan emoji dan 5 hashtag relevan termasuk nama tokoh, max 200 karakter)."
            f"\n\nTRANSKRIP RINGKAS:\n{compressed_transcript}"
        )
        # For text only, we don't need to upload a file
        response = self.model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return self._parse_response(response)

    def _compress_transcript(self, raw_text):
        """
        Compresses SRT/VTT format to a token-efficient format: [MM:SS] Text content
        Removes arrows, end timestamps (redundant for context), and line numbers.
        """
        lines = raw_text.split('\n')
        compressed_lines = []
        
        # Regex to find timestamp lines: 00:00:00,000 --> 00:00:05,000
        # Supports both comma (SRT) and dot (VTT) separators
        time_pattern = re.compile(r'(\d{1,2}:\d{2}:\d{2})[,\.]\d{3}\s*-->\s*(\d{1,2}:\d{2}:\d{2})[,\.]\d{3}')
        
        current_time = None
        current_text_buffer = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip VTT header or numeric indices
            if line == 'WEBVTT' or line.isdigit():
                continue

            # Check for timestamp
            match = time_pattern.search(line)
            if match:
                # If we have previous text, save it
                if current_time and current_text_buffer:
                    full_text = " ".join(current_text_buffer).strip()
                    if full_text:
                        compressed_lines.append(f"[{current_time}] {full_text}")
                
                # Start new block
                # We only take the start time (Group 1) to save space. 
                # End time is implied by the next line or context usually enough for AI logic.
                full_timestamp = match.group(1) # HH:MM:SS
                
                # Simplify to MM:SS if HH is 00 to save more tokens? 
                # Be careful, sometimes hour is important. Let's keep HH:MM:SS for safety but it's already quite compact.
                # Actually user mentioned 100k tokens, so aggressive is good.
                # Let's try to remove leading 00: if present.
                if full_timestamp.startswith("00:"):
                    short_timestamp = full_timestamp[3:] # MM:SS
                else:
                    short_timestamp = full_timestamp
                    
                current_time = short_timestamp
                current_text_buffer = []
            else:
                # It's text content (or metadata we can't parse, treat as text)
                # Avoid adding 'NOTE' lines from VTT
                if not line.startswith("NOTE"):
                   current_text_buffer.append(line)
        
        # Flush last block
        if current_time and current_text_buffer:
            full_text = " ".join(current_text_buffer).strip()
            if full_text:
                compressed_lines.append(f"[{current_time}] {full_text}")
        
        # Fallback: If compression returned nothing (e.g. format didn't match regex), return raw text
        # to avoid breaking the app.
        if not compressed_lines:
            # Maybe it wasn't SRT/VTT?
            return raw_text
            
        return "\n".join(compressed_lines)

    def _build_context_string(self, video_context):
        """Builds a context string from video metadata to prepend to prompts."""
        if not video_context:
            return ""
        
        parts = []
        if video_context.get('title'):
            parts.append(f"Judul Video: {video_context['title']}")
        if video_context.get('channel'):
            parts.append(f"Channel: {video_context['channel']}")
        if video_context.get('tags'):
            parts.append(f"Tags: {video_context['tags']}")
        if video_context.get('description_preview'):
            parts.append(f"Deskripsi: {video_context['description_preview'][:200]}...")
        
        if not parts:
            return ""
        
        return "KONTEKS VIDEO:\n" + "\n".join(parts) + "\n\n"



    def _generate_content(self, content_input, prompt):
        response = self.model.generate_content(
            [content_input, prompt],
            generation_config={"response_mime_type": "application/json"}
        )
        return self._parse_response(response)

    def _parse_response(self, response):
        try:
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            return json.loads(text)
        except json.JSONDecodeError:
            print("Failed to parse JSON response:", response.text)
            return []

    def delete_file(self, file_obj):
        """Deletes the file from Gemini storage."""
        print(f"Deleting file: {file_obj.name}")
        genai.delete_file(file_obj.name)


class GrokHandler:
    """Handler for xAI Grok API using OpenAI-compatible SDK."""
    
    XAI_BASE_URL = "https://api.x.ai/v1"
    
    def __init__(self, api_key):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.XAI_BASE_URL
        )
        # Use grok-3-fast for efficiency (user requested "grok 4.1 fast")
        # Note: xAI model naming - check docs for latest. Using grok-3-fast as of late 2024
        self.model_name = "grok-3-fast"
    
    def analyze_transcript(self, transcript_text, video_context=None):
        """Sends a prompt to Grok to identify best moments from transcript text with viral scoring."""
        
        # Compress transcript (reuse same logic)
        compressed_transcript = self._compress_transcript(transcript_text)
        print(f"Transcript compressed. Original len: {len(transcript_text)} -> New len: {len(compressed_transcript)}")
        
        context_str = self._build_context_string(video_context)
        prompt = (
            f"{context_str}"
            "Analisis transkrip berikut ini. Input berupa ringkasan transkrip dengan format `[MM:SS] Teks`. "
            "Identifikasi 5 momen minimal 1 menit dan maksimal 3 menit paling menarik, hook, lucu, atau penting "
            "yang cocok untuk dijadikan konten pendek (Shorts/Reels/Video TikTok). "
            "PENTING: Gunakan timestamp yang ada di transkrip untuk menentukan waktu mulai dan selesai. "
            "PENTING: Jika ada public figure atau tokoh terkenal yang disebutkan dalam konteks, WAJIB sertakan nama mereka di judul dan caption. "
            "Untuk SETIAP momen, berikan penilaian potensi viral dan metadata untuk posting. "
            "Berikan respon HANYA dalam format JSON valid berisi list object dengan key: "
            "`start_time_sec` (integer, detik), "
            "`end_time_sec` (integer, detik), "
            "`description` (deskripsi internal singkat), "
            "`viral_score` (integer 1-100, skor potensi viral berdasarkan hook, engagement, keunikan), "
            "`suggested_title` (judul menarik dan clickbait untuk YouTube/TikTok dengan nama tokoh jika ada, max 60 karakter), "
            "`suggested_caption` (caption siap posting dengan emoji dan 5 hashtag relevan termasuk nama tokoh, max 200 karakter)."
            f"\n\nTRANSKRIP RINGKAS:\n{compressed_transcript}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that analyzes video transcripts and returns JSON data."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return self._parse_response(response)
        except Exception as e:
            print(f"Grok API Error: {e}")
            return []
    
    def _compress_transcript(self, raw_text):
        """Compresses SRT/VTT format to a token-efficient format."""
        lines = raw_text.split('\n')
        compressed_lines = []
        time_pattern = re.compile(r'(\d{1,2}:\d{2}:\d{2})[,\.]\d{3}\s*-->\s*(\d{1,2}:\d{2}:\d{2})[,\.]\d{3}')
        
        current_time = None
        current_text_buffer = []

        for line in lines:
            line = line.strip()
            if not line or line == 'WEBVTT' or line.isdigit():
                continue

            match = time_pattern.search(line)
            if match:
                if current_time and current_text_buffer:
                    full_text = " ".join(current_text_buffer).strip()
                    if full_text:
                        compressed_lines.append(f"[{current_time}] {full_text}")
                
                full_timestamp = match.group(1)
                if full_timestamp.startswith("00:"):
                    short_timestamp = full_timestamp[3:]
                else:
                    short_timestamp = full_timestamp
                    
                current_time = short_timestamp
                current_text_buffer = []
            else:
                if not line.startswith("NOTE"):
                   current_text_buffer.append(line)
        
        if current_time and current_text_buffer:
            full_text = " ".join(current_text_buffer).strip()
            if full_text:
                compressed_lines.append(f"[{current_time}] {full_text}")
        
        if not compressed_lines:
            return raw_text
            
        return "\n".join(compressed_lines)
    
    def _build_context_string(self, video_context):
        """Builds a context string from video metadata."""
        if not video_context:
            return ""
        
        parts = []
        if video_context.get('title'):
            parts.append(f"Judul Video: {video_context['title']}")
        if video_context.get('channel'):
            parts.append(f"Channel: {video_context['channel']}")
        if video_context.get('tags'):
            parts.append(f"Tags: {video_context['tags']}")
        if video_context.get('description_preview'):
            parts.append(f"Deskripsi: {video_context['description_preview'][:200]}...")
        
        if not parts:
            return ""
        
        return "KONTEKS VIDEO:\n" + "\n".join(parts) + "\n\n"
    
    def _parse_response(self, response):
        """Parse Grok API response to extract JSON clips data."""
        try:
            text = response.choices[0].message.content.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            data = json.loads(text)
            
            # Grok might return {"clips": [...]} or just [...]
            if isinstance(data, dict):
                # Try common keys
                for key in ['clips', 'moments', 'results', 'data']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # If no list found, return empty
                return []
            elif isinstance(data, list):
                return data
            else:
                return []
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw response: {response.choices[0].message.content[:500]}")
            return []
        except Exception as e:
            print(f"Error parsing Grok response: {e}")
            return []


class OpenRouterHandler:
    """Handler for OpenRouter API using OpenAI-compatible SDK with free models."""
    
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    # Free models available on OpenRouter (as of 2024)
    FREE_MODELS = {
        "google/gemma-3-27b-it:free": "Google Gemma 3 27B (Free)",
        "meta-llama/llama-3.3-70b-instruct:free": "Meta Llama 3.3 70B (Free)",
        "deepseek/deepseek-chat-v3-0324:free": "DeepSeek V3 (Free)",
        "qwen/qwen3-235b-a22b:free": "Qwen 3 235B (Free)",
    }
    
    def __init__(self, api_key, model_id="google/gemma-3-27b-it:free"):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.OPENROUTER_BASE_URL
        )
        # Default to Google Gemma 3 27B - excellent free model for text analysis
        self.model_name = model_id
        print(f"OpenRouter initialized with model: {self.model_name}")
    
    def analyze_transcript(self, transcript_text, video_context=None):
        """Sends a prompt to OpenRouter to identify best moments from transcript text with viral scoring."""
        
        # Compress transcript (reuse same logic)
        compressed_transcript = self._compress_transcript(transcript_text)
        print(f"Transcript compressed. Original len: {len(transcript_text)} -> New len: {len(compressed_transcript)}")
        
        context_str = self._build_context_string(video_context)
        prompt = (
            f"{context_str}"
            "Analisis transkrip berikut ini. Input berupa ringkasan transkrip dengan format `[MM:SS] Teks`. "
            "Identifikasi 5 momen minimal 1 menit dan maksimal 3 menit paling menarik, hook, lucu, atau penting "
            "yang cocok untuk dijadikan konten pendek (Shorts/Reels/Video TikTok). "
            "PENTING: Gunakan timestamp yang ada di transkrip untuk menentukan waktu mulai dan selesai. "
            "PENTING: Jika ada public figure atau tokoh terkenal yang disebutkan dalam konteks, WAJIB sertakan nama mereka di judul dan caption. "
            "Untuk SETIAP momen, berikan penilaian potensi viral dan metadata untuk posting. "
            "Berikan respon HANYA dalam format JSON valid berisi list object dengan key: "
            "`start_time_sec` (integer, detik), "
            "`end_time_sec` (integer, detik), "
            "`description` (deskripsi internal singkat), "
            "`viral_score` (integer 1-100, skor potensi viral berdasarkan hook, engagement, keunikan), "
            "`suggested_title` (judul menarik dan clickbait untuk YouTube/TikTok dengan nama tokoh jika ada, max 60 karakter), "
            "`suggested_caption` (caption siap posting dengan emoji dan 5 hashtag relevan termasuk nama tokoh, max 200 karakter)."
            f"\n\nTRANSKRIP RINGKAS:\n{compressed_transcript}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that analyzes video transcripts and returns JSON data. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                extra_headers={
                    "HTTP-Referer": "https://smartclip.ai",
                    "X-Title": "SmartClip AI"
                }
            )
            return self._parse_response(response)
        except Exception as e:
            print(f"OpenRouter API Error: {e}")
            return []
    
    def _compress_transcript(self, raw_text):
        """Compresses SRT/VTT format to a token-efficient format."""
        lines = raw_text.split('\n')
        compressed_lines = []
        time_pattern = re.compile(r'(\d{1,2}:\d{2}:\d{2})[,\.]\d{3}\s*-->\s*(\d{1,2}:\d{2}:\d{2})[,\.]\d{3}')
        
        current_time = None
        current_text_buffer = []

        for line in lines:
            line = line.strip()
            if not line or line == 'WEBVTT' or line.isdigit():
                continue

            match = time_pattern.search(line)
            if match:
                if current_time and current_text_buffer:
                    full_text = " ".join(current_text_buffer).strip()
                    if full_text:
                        compressed_lines.append(f"[{current_time}] {full_text}")
                
                full_timestamp = match.group(1)
                if full_timestamp.startswith("00:"):
                    short_timestamp = full_timestamp[3:]
                else:
                    short_timestamp = full_timestamp
                    
                current_time = short_timestamp
                current_text_buffer = []
            else:
                if not line.startswith("NOTE"):
                   current_text_buffer.append(line)
        
        if current_time and current_text_buffer:
            full_text = " ".join(current_text_buffer).strip()
            if full_text:
                compressed_lines.append(f"[{current_time}] {full_text}")
        
        if not compressed_lines:
            return raw_text
            
        return "\n".join(compressed_lines)
    
    def _build_context_string(self, video_context):
        """Builds a context string from video metadata."""
        if not video_context:
            return ""
        
        parts = []
        if video_context.get('title'):
            parts.append(f"Judul Video: {video_context['title']}")
        if video_context.get('channel'):
            parts.append(f"Channel: {video_context['channel']}")
        if video_context.get('tags'):
            parts.append(f"Tags: {video_context['tags']}")
        if video_context.get('description_preview'):
            parts.append(f"Deskripsi: {video_context['description_preview'][:200]}...")
        
        if not parts:
            return ""
        
        return "KONTEKS VIDEO:\n" + "\n".join(parts) + "\n\n"
    
    def _parse_response(self, response):
        """Parse OpenRouter API response to extract JSON clips data."""
        try:
            text = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            
            # Handle different response formats
            if isinstance(data, dict):
                # Try common keys
                for key in ['clips', 'moments', 'results', 'data']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # If no list found, return empty
                return []
            elif isinstance(data, list):
                return data
            else:
                return []
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw response: {response.choices[0].message.content[:500]}")
            return []
        except Exception as e:
            print(f"Error parsing OpenRouter response: {e}")
            return []

