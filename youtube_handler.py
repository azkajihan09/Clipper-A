import yt_dlp
import os
from config import get_ffmpeg_path

# Custom Logger to suppress technical warnings
class QuietLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        # Filter out specific unwanted warnings
        if "no supported javascript runtime" in msg.lower():
            return
        if "sabr streaming" in msg.lower():
            return
        if "missing a url" in msg.lower():
            return
        print(f"Warning: {msg}")

    def error(self, msg):
        print(f"Error: {msg}")

class YouTubeHandler:
    # Supported browsers for cookie extraction
    SUPPORTED_BROWSERS = ['chrome', 'firefox', 'edge', 'opera', 'brave', 'chromium']
    
    def __init__(self, output_dir="Downloads", use_cookies_from=None):
        """
        Args:
            output_dir: Directory to save downloaded files
            use_cookies_from: Browser name to extract cookies from (chrome, firefox, edge, etc.)
                              Set to None to disable, or 'auto' to try common browsers.
        """
        self.output_dir = output_dir
        self.use_cookies_from = use_cookies_from
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _get_cookie_opts(self):
        """Returns yt-dlp options for cookie extraction from browser."""
        if not self.use_cookies_from:
            return {}
        
        if self.use_cookies_from == 'auto':
            # Try to detect available browser
            for browser in ['chrome', 'firefox', 'edge']:
                try:
                    # Test if browser cookies can be accessed
                    test_opts = {'cookiesfrombrowser': (browser,), 'quiet': True}
                    return {'cookiesfrombrowser': (browser,)}
                except:
                    continue
            return {}
        else:
            return {'cookiesfrombrowser': (self.use_cookies_from,)}

    def _get_active_cookie_opts(self):
        """Helper to get the best available cookie options (file > browser)."""
        cookie_file = os.path.join(self.output_dir, "cookies.txt")
        if os.path.exists(cookie_file):
            return {'cookiefile': cookie_file}
        return self._get_cookie_opts()

    def _ensure_cookie_file(self):
        """
        Exports cookies from the selected browser to a temporary file using yt-dlp.
        Returns: Path to the cookie file, or None if failed/not configured.
        """
        if not self.use_cookies_from or self.use_cookies_from == 'None':
            return None
            
        cookie_file = os.path.join(self.output_dir, "cookies.txt")
        
        # Check if cookie file is fresh (less than 1 hour old)
        if os.path.exists(cookie_file):
            import time
            if time.time() - os.path.getmtime(cookie_file) < 3600:
                return os.path.abspath(cookie_file)

        # Export cookies using yt-dlp
        # We use a dummy URL to trigger the cookie extraction
        try:
            browser_arg = self.use_cookies_from
            if browser_arg == 'auto':
                # Try chrome as default for export if auto
                browser_arg = 'chrome' 
                
            cmd = f'yt-dlp --cookies-from-browser {browser_arg} --cookies "{cookie_file}" --skip-download "https://www.youtube.com"'
            
            # Using subprocess to run command
            import subprocess
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            
            if os.path.exists(cookie_file):
                return os.path.abspath(cookie_file)
        except Exception as e:
            print(f"Cookie export failed: {e}")
            
        return None

    def get_video_metadata(self, url, progress_callback=None):
        """
        Extracts video metadata (title, channel, tags, description) without downloading.
        Returns: Dict with 'title', 'channel', 'tags', 'description_preview'
        """
        if progress_callback: progress_callback("Fetching video metadata...")
        
        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
            **self._get_active_cookie_opts(),  # Add browser cookies
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                title = info.get('title', '')
                channel = info.get('uploader', info.get('channel', ''))
                tags = info.get('tags', []) or []
                description = info.get('description', '')
                
                # Get first 500 chars of description for context
                description_preview = description[:500] if description else ''
                
                # Combine tags into comma-separated string
                tags_str = ', '.join(tags[:10]) if tags else ''  # Max 10 tags
                
                if progress_callback:
                    progress_callback(f"Video: {title[:50]}... by {channel}")
                
                return {
                    'title': title,
                    'channel': channel,
                    'tags': tags_str,
                    'description_preview': description_preview
                }
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return {
                'title': '',
                'channel': '',
                'tags': '',
                'description_preview': ''
            }


    def download_for_analysis(self, url, progress_callback=None, running_event=None):
        """
        Downloads low resolution video for AI analysis.
        Returns: Absolute path to the downloaded file
        """
        ffmpeg_path = get_ffmpeg_path()
        
        ydl_opts = {
            # Download worst quality that is still mp4 (for compatibility)
            'format': 'worst[ext=mp4]/worst', 
            'outtmpl': os.path.join(self.output_dir, 'analysis_%(id)s.%(ext)s'),
            'ffmpeg_location': ffmpeg_path,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'overwrites': True,
            'logger': QuietLogger(),
            **self._get_active_cookie_opts(),
        }

        if progress_callback:
            def progress_hook(d):
                if running_event and not running_event.is_set():
                    raise Exception("Process Cancelled")
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '0%').replace('%','')
                    try:
                        progress_callback(f"Downloading (Low Res): {p}%")
                    except:
                        pass
            ydl_opts['progress_hooks'] = [progress_hook]

        try:
            if progress_callback: progress_callback(f"Fetching video info for analysis: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return os.path.abspath(filename)
        except Exception as e:
            raise Exception(f"Analysis Download Failed: {str(e)}")

    def download_clip(self, url, start, end, title, output_dir="Output", progress_callback=None, running_event=None):
        """
        Downloads a specific section of the video in high quality.
        """
        ffmpeg_path = get_ffmpeg_path()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Sanitize title
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '_', '-')]).strip()
        safe_title = safe_title.replace(" ", "_")
        if not safe_title:
            safe_title = f"clip_{int(start)}_{int(end)}"
        output_filename = f"{safe_title}.mp4"
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(output_dir, output_filename),
            'ffmpeg_location': ffmpeg_path,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            # Use download_ranges to download only the specific section
            'download_ranges': lambda _, __: [{'start_time': start, 'end_time': end}],
            'force_keyframes_at_cuts': True,
            'logger': QuietLogger(),
            **self._get_active_cookie_opts(), 
        }

        if progress_callback:
            def progress_hook(d):
                if running_event and not running_event.is_set():
                    raise Exception("Process Cancelled")
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '0%').replace('%','')
                    try:
                        progress_callback(f"Downloading Clip '{safe_title}': {p}%")
                    except:
                        pass
            ydl_opts['progress_hooks'] = [progress_hook]

        try:
            # Attempt 1: Try with force_keyframes_at_cuts (Best precision)
            print(f"Downloading clip (High Precision): {start} - {end}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                return os.path.join(output_dir, output_filename)
        except Exception as e:
            print(f"High precision download failed: {e}")
            if "ffmpeg exited with code" in str(e) or "4294967274" in str(e):
                print("Retrying with standard precision...")
                try:
                    # Attempt 2: Disable force_keyframes_at_cuts (More robust)
                    ydl_opts['force_keyframes_at_cuts'] = False
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                        return os.path.join(output_dir, output_filename)
                except Exception as e2:
                    print(f"Clip Download Failed (Retry): {e2}")
                    return None
            else:
                 print(f"Clip Download Failed: {e}")
                 return None

    def download_audio(self, url, progress_callback=None, running_event=None):
        """
        Downloads audio only (m4a/mp3) for AI analysis.
        """
        ffmpeg_path = get_ffmpeg_path()
        
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl': os.path.join(self.output_dir, 'analysis_audio_%(id)s.%(ext)s'),
            'ffmpeg_location': ffmpeg_path,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
            **self._get_active_cookie_opts(),
        }

        if progress_callback:
            def progress_hook(d):
                if running_event and not running_event.is_set():
                    raise Exception("Process Cancelled")
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '0%').replace('%','')
                    try:
                        progress_callback(f"Downloading Audio: {p}%")
                    except:
                        pass
            ydl_opts['progress_hooks'] = [progress_hook]

        try:
            if progress_callback: progress_callback(f"Fetching audio info for analysis: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return os.path.abspath(filename)
        except Exception as e:
            raise Exception(f"Audio Download Failed: {str(e)}")

    def download_video(self, url, progress_callback=None, running_event=None):
        """
        Downloads a video from YouTube.
        url: YouTube URL
        progress_callback: Optional function to call with status updates (str)
        Returns: Absolute path to the downloaded file
        """
        ffmpeg_path = get_ffmpeg_path()
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'ffmpeg_location': ffmpeg_path, # Use our configured ffmpeg
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            **self._get_active_cookie_opts(),
        }

        # Add progress hook if callback provided
        if progress_callback:
            def progress_hook(d):
                if running_event and not running_event.is_set():
                    raise Exception("Process Cancelled")
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '0%').replace('%','')
                    try:
                        progress_callback(f"Downloading: {p}%")
                    except:
                        pass
                elif d['status'] == 'finished':
                    progress_callback("Download complete. Processing...")
            
            ydl_opts['progress_hooks'] = [progress_hook]

        try:
            if progress_callback: progress_callback(f"Fetching video info for: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return os.path.abspath(filename)
                
        except Exception as e:
            raise Exception(f"YouTube Download Failed: {str(e)}")

    def get_transcript(self, url, progress_callback=None, keep_vtt=False, target_language=None):
        """
        Downloads and parses the auto-generated subtitle (or manual if available).
        Args:
            keep_vtt: If True, keeps the VTT file and returns (transcript, vtt_path) tuple.
            target_language: 'id' or 'en'. If set, strictly tries to get that language (translating if needed for ID).
        Returns: 
            If keep_vtt=False: String containing the transcript with timestamps, or None if failed.
            If keep_vtt=True: Tuple (transcript_string, vtt_path) or (None, None) if failed.
        """
        import re
        import time
        from youtube_transcript_api import YouTubeTranscriptApi
        from xml.parsers.expat import ExpatError
        
        if progress_callback: progress_callback(f"Checking for subtitles ({target_language if target_language else 'Auto'})...")
        
        # Save to persistent folder if keeping, otherwise temp
        if keep_vtt:
            sub_dir = os.path.join(self.output_dir, "subtitles")
        else:
            sub_dir = os.path.join(self.output_dir, "temp_subs")
            
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)

        # Extract video ID from URL first
        video_id = None
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info['id']
        except:
            # Fallback regex extraction if yt-dlp fails just to get ID
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
            if match:
                video_id = match.group(1)

        # 1. Attempt using YouTubeTranscriptApi (Smart Auto-Translate)
        if video_id:
            try:
                if progress_callback: progress_callback("Fetching via API (Smart Mode)...")
                
                # Use cookies if available to prevent 429
                cookie_file = self._ensure_cookie_file()
                if cookie_file and progress_callback:
                     progress_callback("Using browser cookies for API...")
                
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, cookies=cookie_file)
                
                target_transcript = None
                
                # Define strategies based on target_language
                if target_language == 'id':
                    # Strategy for INDONESIAN
                    # 1. Manual ID
                    try:
                        target_transcript = transcript_list.find_manually_created_transcript(['id'])
                        if progress_callback: progress_callback("Found manual Indonesian subtitles.")
                    except: pass
                    
                    # 2. Translate Manual English -> ID
                    if not target_transcript:
                        try:
                            source_transcript = transcript_list.find_manually_created_transcript(['en', 'en-US'])
                            target_transcript = source_transcript.translate('id')
                            if progress_callback: progress_callback("Translating manual English subs to Indonesian...")
                        except: pass

                    # 3. Auto ID
                    if not target_transcript:
                        try:
                            target_transcript = transcript_list.find_generated_transcript(['id'])
                            if progress_callback: progress_callback("Found auto-generated Indonesian subs.")
                        except: pass

                    # 4. Translate Auto English -> ID
                    if not target_transcript:
                        try:
                            source_transcript = transcript_list.find_generated_transcript(['en', 'en-US'])
                            target_transcript = source_transcript.translate('id')
                            if progress_callback: progress_callback("Translating auto-generated subs to Indonesian...")
                        except: pass
                        
                elif target_language == 'en':
                    # Strategy for ENGLISH
                    # 1. Manual EN
                    try:
                        target_transcript = transcript_list.find_manually_created_transcript(['en', 'en-US'])
                        if progress_callback: progress_callback("Found manual English subtitles.")
                    except: pass
                    
                    # 2. Auto EN
                    if not target_transcript:
                        try:
                            target_transcript = transcript_list.find_generated_transcript(['en', 'en-US'])
                            if progress_callback: progress_callback("Found auto-generated English subs.")
                        except: pass
                        
                else: 
                    # LEGACY / AUTO STRATEGY (Prioritize ID, fallback to EN)
                    # Priority 1: Manual Indonesian
                    try:
                        target_transcript = transcript_list.find_manually_created_transcript(['id'])
                        if progress_callback: progress_callback("Found manual Indonesian subtitles.")
                    except: pass
                    
                    # Priority 2: Translated to Indonesian (from any manual source)
                    if not target_transcript:
                        try:
                            source_transcript = transcript_list.find_manually_created_transcript(['en', 'en-US'])
                            target_transcript = source_transcript.translate('id')
                            if progress_callback: progress_callback("Translating manual English subs to Indonesian...")
                        except: pass
                            
                    # Priority 3: Auto-Generated Indonesian (rare but possible)
                    if not target_transcript:
                        try:
                            target_transcript = transcript_list.find_generated_transcript(['id'])
                            if progress_callback: progress_callback("Found auto-generated Indonesian subs.")
                        except: pass

                    # Priority 4: Translate Auto-Generated English to Indonesian
                    if not target_transcript:
                        try:
                            source_transcript = transcript_list.find_generated_transcript(['en', 'en-US'])
                            target_transcript = source_transcript.translate('id')
                            if progress_callback: progress_callback("Translating auto-generated subs to Indonesian...")
                        except: pass

                    # Priority 5: Fallback to English (Manual then Generated) matches
                    if not target_transcript:
                         try:
                            target_transcript = transcript_list.find_transcript(['en', 'en-US'])
                            if progress_callback: progress_callback("Fallback: Using English subtitles.")
                         except: pass

                if target_transcript:
                    fetched_transcript = target_transcript.fetch()
                    
                    # Format for AI Analysis
                    formatted_transcript = []
                    for entry in fetched_transcript:
                        start = int(entry['start'])
                        m, s = divmod(start, 60)
                        h, m = divmod(m, 60)
                        timestamp = f"{h:02d}:{m:02d}:{s:02d}"
                        formatted_transcript.append(f"[{timestamp}] {entry['text']}")
                    
                    transcript_text = "\n".join(formatted_transcript)
                    
                    vtt_path = None
                    if keep_vtt:
                        vtt_filename = f"{video_id}.vtt"
                        vtt_path = os.path.join(sub_dir, vtt_filename)
                        self._save_json_as_vtt(fetched_transcript, vtt_path)
                        if progress_callback: progress_callback(f"Subtitle saved (API): {vtt_filename}")
                        return transcript_text, os.path.abspath(vtt_path)
                    else:
                        return transcript_text
                else:
                    if target_language:
                        raise Exception(f"No suitable transcript found for language: {target_language}")
                    else:
                        raise Exception("No suitable transcript found.")

            except Exception as e:
                # If API fails (e.g. disabled on video), fall back seamlessly
                if isinstance(e, ExpatError) or "no element found" in str(e):
                     pass # Silent fail for XML parsing errors (common with API blocks)
                elif "TranscriptsDisabled" not in str(e) and "NoTranscriptFound" not in str(e):
                     if progress_callback: progress_callback(f"API Fetch issue: {str(e)[:50]}...")
                # Fall through to yt-dlp method
                if target_language: 
                     # If strict language was requested and API failed, we might want to be strict with yt-dlp too
                     pass 

        # 2. Fallback: Check if subtitle already exists (CACHE) from previous yt-dlp runs
        if video_id:
            for f in os.listdir(sub_dir):
                if f.startswith(video_id) and (f.endswith('.vtt') or f.endswith('.srt')):
                    sub_path = os.path.join(sub_dir, f)
                    if progress_callback: progress_callback(f"Using cached subtitle: {f}")
                    transcript = self._parse_subtitle_file(sub_path)
                    if keep_vtt:
                        return transcript, os.path.abspath(sub_path)
                    else:
                        return transcript
        
        # Prepare yt-dlp fallback options based on language
        langs_to_try = ['id', 'en']
        if target_language == 'id':
            langs_to_try = ['id']
        elif target_language == 'en':
            langs_to_try = ['en']

        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': langs_to_try,
            'subtitlesformat': 'vtt/srt/best',
            'outtmpl': os.path.join(sub_dir, '%(id)s'),
            'quiet': True,
            'no_warnings': True,
            **self._get_active_cookie_opts(),
        }

        # Retry logic for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_id = info['id']
                    
                    # Find the downloaded vtt/srt file
                    sub_path = None
                    for f in os.listdir(sub_dir):
                        if f.startswith(video_id) and (f.endswith('.vtt') or f.endswith('.srt')):
                            sub_path = os.path.join(sub_dir, f)
                            break
                    
                    if not sub_path:
                        if progress_callback: progress_callback("No subtitles found.")
                        return (None, None) if keep_vtt else None

                    # Parse VTT/SRT
                    if progress_callback: progress_callback(f"Parsing subtitles ({os.path.splitext(sub_path)[1]})...")
                    transcript = self._parse_subtitle_file(sub_path)
                    
                    if keep_vtt:
                        # Return both transcript and path
                        if progress_callback: progress_callback(f"Subtitle saved: {os.path.basename(sub_path)}")
                        return transcript, os.path.abspath(sub_path)
                    else:
                        # Cleanup if not keeping
                        try:
                            os.remove(sub_path)
                            os.rmdir(sub_dir)
                        except:
                            pass
                        return transcript
            except Exception as e:
                error_str = str(e)
                if "429" in error_str and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                    if progress_callback: 
                        progress_callback(f"Rate limited. Waiting {wait_time}s before retry ({attempt+1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Transcript Error: {e}")
                    return (None, None) if keep_vtt else None
        
        return (None, None) if keep_vtt else None

    def _save_json_as_vtt(self, transcript_list, output_path):
        """Converts YouTube API transcript list to VTT format."""
        
        def format_time(seconds):
            # Format: HH:MM:SS.mmm
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            ms = int((seconds * 1000) % 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            for entry in transcript_list:
                start = entry['start']
                duration = entry['duration']
                end = start + duration
                text = entry['text']
                
                f.write(f"{format_time(start)} --> {format_time(end)}\n")
                f.write(f"{text}\n\n")

    def download_subtitle(self, url, progress_callback=None):
        """
        Downloads subtitle file (VTT/SRT) and returns the path.
        """
        if progress_callback: progress_callback("Downloading subtitles...")
        
        # Save to Downloads folder
        sub_dir = os.path.join(self.output_dir, "subtitles")
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)

        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['id', 'en'],
            'subtitlesformat': 'vtt/srt/best',
            'outtmpl': os.path.join(sub_dir, '%(id)s'),
            'quiet': True,
            'no_warnings': True,
            **self._get_active_cookie_opts(),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info['id']
                
                # Find the downloaded file
                sub_path = None
                for f in os.listdir(sub_dir):
                    if f.startswith(video_id) and (f.endswith('.vtt') or f.endswith('.srt')):
                        sub_path = os.path.join(sub_dir, f)
                        break
                
                if not sub_path:
                    if progress_callback: progress_callback("No subtitles found for download.")
                    return None

                if progress_callback: progress_callback(f"Subtitle saved: {os.path.basename(sub_path)}")
                return os.path.abspath(sub_path)

        except Exception as e:
            print(f"Subtitle Download Error: {e}")
            return None

    def _parse_subtitle_file(self, file_path):
        import re
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            transcript = []
            
            # Identify format
            is_vtt = 'WEBVTT' in content[:100]
            
            if is_vtt:
                timestamp_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})')
            else: # Assume SRT
                timestamp_pattern = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})')
            
            current_timestamp = None
            seen_lines = set()
            
            for line in lines:
                line = line.strip()
                if not line: continue
                if is_vtt and (line == 'WEBVTT' or line.startswith('NOTE')): continue
                if not is_vtt and line.isdigit(): continue # Skip SRT indices
                
                match = timestamp_pattern.search(line)
                if match:
                    # Normalize timestamp format to HH:MM:SS
                    raw_ts = match.group(1)
                    if ',' in raw_ts: # SRT uses comma
                        current_timestamp = raw_ts.split(',')[0]
                    else: # VTT uses dot
                        current_timestamp = raw_ts.split('.')[0]
                elif current_timestamp:
                    # Clean tags
                    line = re.sub(r'<[^>]+>', '', line)
                    # Deduplicate 
                    if line not in seen_lines:
                        transcript.append(f"[{current_timestamp}] {line}")
                        seen_lines.add(line)
                        if len(transcript) > 1 and transcript[-2].endswith(line):
                             transcript.pop()
            
            return "\n".join(transcript)
        except Exception as e:
            print(f"Subtitle Parse Error: {e}")
            return None


