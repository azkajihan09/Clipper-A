# === SUPPRESS MEDIAPIPE C++ WARNINGS ===
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

import ffmpeg
import cv2
import numpy as np
import mediapipe as mp
from config import get_ffmpeg_path

class PlatformOptimizer:
    """
    Platform-specific optimization for social media platforms
    """
    
    PLATFORM_SPECS = {
        "TikTok": {
            "aspect_ratio": (9, 16),
            "resolution": (1080, 1920),
            "max_duration": 600,  # 10 minutes
            "optimal_duration": (15, 60),  # 15-60 seconds
            "fps": 30,
            "bitrate": "8M",
            "audio_bitrate": "192k",
            "description": "TikTok Vertical (9:16)"
        },
        "YouTube Shorts": {
            "aspect_ratio": (9, 16),
            "resolution": (1080, 1920),
            "max_duration": 60,
            "optimal_duration": (15, 60),
            "fps": 30,
            "bitrate": "10M",
            "audio_bitrate": "192k",
            "description": "YouTube Shorts (9:16)"
        },
        "Instagram Reels": {
            "aspect_ratio": (9, 16),
            "resolution": (1080, 1920),
            "max_duration": 90,
            "optimal_duration": (15, 30),
            "fps": 30,
            "bitrate": "8M",
            "audio_bitrate": "192k",
            "description": "Instagram Reels (9:16)"
        },
        "Instagram Post": {
            "aspect_ratio": (1, 1),
            "resolution": (1080, 1080),
            "max_duration": 60,
            "optimal_duration": (15, 60),
            "fps": 30,
            "bitrate": "6M",
            "audio_bitrate": "128k",
            "description": "Instagram Post Square (1:1)"
        },
        "Instagram Story": {
            "aspect_ratio": (9, 16),
            "resolution": (1080, 1920),
            "max_duration": 15,
            "optimal_duration": (5, 15),
            "fps": 30,
            "bitrate": "8M",
            "audio_bitrate": "192k",
            "description": "Instagram Story (9:16)"
        },
        "Facebook Video": {
            "aspect_ratio": (16, 9),
            "resolution": (1920, 1080),
            "max_duration": 240,  # 4 minutes
            "optimal_duration": (60, 120),
            "fps": 30,
            "bitrate": "8M",
            "audio_bitrate": "192k",
            "description": "Facebook Video Landscape (16:9)"
        },
        "Twitter Video": {
            "aspect_ratio": (16, 9),
            "resolution": (1280, 720),
            "max_duration": 140,  # 2:20
            "optimal_duration": (30, 60),
            "fps": 30,
            "bitrate": "6M",
            "audio_bitrate": "128k",
            "description": "Twitter Video (16:9)"
        },
        "LinkedIn Video": {
            "aspect_ratio": (16, 9),
            "resolution": (1920, 1080),
            "max_duration": 600,  # 10 minutes
            "optimal_duration": (30, 90),
            "fps": 30,
            "bitrate": "10M",
            "audio_bitrate": "192k",
            "description": "LinkedIn Video (16:9)"
        },
        "YouTube Standard": {
            "aspect_ratio": (16, 9),
            "resolution": (1920, 1080),
            "max_duration": None,  # No limit
            "optimal_duration": (60, 300),  # 1-5 minutes
            "fps": 30,
            "bitrate": "12M",
            "audio_bitrate": "192k",
            "description": "YouTube Standard (16:9)"
        }
    }
    
    @classmethod
    def get_platform_list(cls):
        """Return list of available platforms"""
        return list(cls.PLATFORM_SPECS.keys())
    
    @classmethod
    def get_platform_spec(cls, platform):
        """Get specifications for a specific platform"""
        return cls.PLATFORM_SPECS.get(platform, cls.PLATFORM_SPECS["TikTok"])
    
    @classmethod
    def validate_duration(cls, platform, duration_sec):
        """Check if video duration is suitable for platform"""
        spec = cls.get_platform_spec(platform)
        max_dur = spec.get("max_duration")
        optimal_dur = spec.get("optimal_duration", (0, 9999))
        
        warnings = []
        
        if max_dur and duration_sec > max_dur:
            warnings.append(f"Video ({duration_sec}s) exceeds {platform} maximum duration ({max_dur}s)")
            
        if duration_sec < optimal_dur[0]:
            warnings.append(f"Video ({duration_sec}s) is shorter than optimal for {platform} ({optimal_dur[0]}-{optimal_dur[1]}s)")
        elif duration_sec > optimal_dur[1]:
            warnings.append(f"Video ({duration_sec}s) is longer than optimal for {platform} ({optimal_dur[0]}-{optimal_dur[1]}s)")
            
        return warnings
    
    @classmethod
    def get_optimization_tips(cls, platform, current_duration=None):
        """Get optimization tips for the platform"""
        spec = cls.get_platform_spec(platform)
        tips = []
        
        tips.append(f"📱 Target: {spec['description']}")
        tips.append(f"📐 Resolution: {spec['resolution'][0]}x{spec['resolution'][1]}")
        tips.append(f"⏱️ Optimal Duration: {spec['optimal_duration'][0]}-{spec['optimal_duration'][1]} seconds")
        
        if current_duration:
            warnings = cls.validate_duration(platform, current_duration)
            if warnings:
                tips.extend([f"⚠️ {warning}" for warning in warnings])
            else:
                tips.append("✅ Duration is optimal for this platform")
                
        return tips

class VideoProcessor:
    def __init__(self, output_dir="Output", render_device="cpu"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Setup Render Codec
        self.render_device = render_device.lower()
        if self.render_device == "nvidia":
            self.video_codec = "h264_nvenc"
            print("Using NVIDIA GPU (h264_nvenc)")
        elif self.render_device == "amd":
            self.video_codec = "h264_amf"
            print("Using AMD GPU (h264_amf)")
        else:
            self.video_codec = "libx264"
            print("Using CPU (libx264)")

        # Setup FFmpeg path
        self._setup_ffmpeg()

    def _setup_ffmpeg(self):
        ffmpeg_path = get_ffmpeg_path()
        # Check if ffmpeg.exe is in the path provided or in a bin subdirectory
        possible_paths = [
            ffmpeg_path,
            os.path.join(ffmpeg_path, 'bin'),
        ]
        
        found = False
        for path in possible_paths:
            if os.path.exists(os.path.join(path, 'ffmpeg.exe')):
                os.environ["PATH"] += os.pathsep + path
                print(f"FFmpeg found and added to PATH: {path}")
                found = True
                break
        
        if not found:
            print(f"WARNING: ffmpeg.exe not found in {ffmpeg_path}. Ensure it is installed correctly.")

    def _get_ffmpeg_safe_path(self, path):
        """
        Returns a path safe for FFmpeg filters on Windows.
        Preferentially uses relative paths with forward slashes to avoid escaping hell.
        """
        if not path: return path
        
        # Try to make relative to CWD
        try:
            rel_path = os.path.relpath(path, os.getcwd())
            if not rel_path.startswith(".."):
                 # It is inside CWD, safe to use relative
                 return rel_path.replace("\\", "/")
        except:
            pass
            
        # Fallback to absolute path with robust escaping
        # Escape backslashes for string, then colons for filter
        # On Windows, 'D:/foo' in filter usually needs 'D\\:/foo' (escaped colon)
        # But some versions strictly want 'D\:/foo' which means passing 'D\\:...'
        # Let's trust relative path for now, but if forced abs:
        abs_path = os.path.abspath(path).replace("\\", "/")
        # Escape colon: D:/ -> D\:/
        # In Python string literal, "\\" is one backslash. 
        # So we want result string "D\:/". 
        # To get "\:", we need replace(":","\\:")
        return abs_path.replace(":", "\\\\:")

    def cut_video_segment(self, source_path, start, end, output_filename):
        """Cuts a single segment from the video."""
        output_path = os.path.join(self.output_dir, output_filename)
        print(f"Clipping: {output_path} ({start} - {end})")
        try:
            (
                ffmpeg
                .input(source_path, ss=start, to=end)
                .output(output_path, vcodec=self.video_codec, acodec='aac') 
                .overwrite_output()
                .run(quiet=False)
            )
            return output_path
        except ffmpeg.Error as e:
            print(f"Error clipping {output_filename}: {e}")
            if e.stderr:
                print(f"FFmpeg stderr: {e.stderr.decode('utf8')}")
            return None

    def clip_video(self, source_path, clips):
        """
        Clips the video based on the provided list of clips.
        clips: List of dicts with 'start_time_sec', 'end_time_sec', 'description'
        """
        results = []
        for i, clip in enumerate(clips):
            start = clip.get('start_time_sec')
            end = clip.get('end_time_sec')
            if start is None: start = clip.get('start_time')
            if end is None: end = clip.get('end_time')

            desc = clip['description'].replace(" ", "_").replace("/", "-")
            output_filename = f"clip_{i+1}_{desc}.mp4"
            
            path = self.cut_video_segment(source_path, start, end, output_filename)
            if path:
                results.append(path)
        
        return results

    def extract_audio(self, video_path):
        """Extracts audio from video file for AI analysis."""
        base, _ = os.path.splitext(video_path)
        output_path = f"{base}_audio.m4a"
        
        print(f"Extracting audio to: {output_path}")
        try:
            (
                ffmpeg
                .input(video_path)
                .output(output_path, acodec='aac', vn=None, loglevel="quiet")
                .overwrite_output()
                .run()
            )
            return output_path
        except ffmpeg.Error as e:
            print(f"Error extracting audio: {e}")
            return None

    def extract_transcript(self, video_path):
        """
        Extracts embedded subtitles from video file (if available) as text.
        Returns: String contains transcript or None
        """
        # 1. Probe for subtitle streams
        try:
            probe = ffmpeg.probe(video_path)
            subtitle_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'subtitle']
            
            if not subtitle_streams:
                print("No subtitle streams found in file.")
                return None
            
            # 2. Extract first subtitle stream to vtt
            base, _ = os.path.splitext(video_path)
            output_vtt = f"{base}_temp_subs.vtt"
            
            # Map the first subtitle stream (0:s:0)
            (
                ffmpeg
                .input(video_path)
                .output(output_vtt, map='0:s:0', quiet=True)
                .overwrite_output()
                .run()
            )
            
            # 3. Read and parse VTT (Reuse simple parsing logic or just read text)
            # Simple read for now - LLM can handle raw VTT usually
            if os.path.exists(output_vtt):
                 with open(output_vtt, 'r', encoding='utf-8', errors='ignore') as f:
                     content = f.read()
                 
                 # cleanup
                 try:
                     os.remove(output_vtt)
                 except:
                     pass
                     
                 return content
            return None
            
        except ffmpeg.Error as e:
            print(f"Error extracting subtitles: {e}")
            return None

    def slice_subtitle(self, subtitle_path, start_sec, end_sec, output_path=None):
        """
        Slices a VTT/SRT subtitle file and creates CapCut-style short captions.
        - Max 6-8 words per caption entry
        - No overlapping timestamps
        - Clean, short phrases for easy reading
        Returns: Path to the sliced subtitle file.
        """
        import re
        
        if not os.path.exists(subtitle_path):
            print(f"Subtitle file not found: {subtitle_path}")
            return None
        
        # Always output as SRT (better compatibility with FFmpeg)
        if not output_path:
            base = os.path.splitext(subtitle_path)[0]
            output_path = f"{base}_clip_{int(start_sec)}_{int(end_sec)}.srt"
        
        # Read source file
        try:
            with open(subtitle_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading subtitle: {e}")
            return None
        
        # Parse timestamps
        timestamp_pattern = re.compile(
            r'(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})'
        )
        
        def time_to_sec(time_str):
            time_str = time_str.replace(',', '.')
            parts = time_str.split(':')
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        
        def sec_to_srt_time(seconds):
            """Convert seconds to SRT timestamp format (00:00:00,000)."""
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = seconds % 60
            return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.', ',')
        
        # Collect all text with timing from full VTT
        all_segments = []  # List of (start, end, text)
        
        blocks = re.split(r'\n\n+', content)
        for block in blocks:
            block = block.strip()
            if not block or block == 'WEBVTT' or block.startswith('NOTE'):
                continue
            
            match = timestamp_pattern.search(block)
            if not match:
                continue
            
            block_start = time_to_sec(match.group(1))
            block_end = time_to_sec(match.group(2))
            
            # Skip if outside our clip range
            if block_end < start_sec or block_start > end_sec:
                continue
            
            # Get text content
            lines = block.split('\n')
            text_lines = []
            found_timestamp = False
            for line in lines:
                if timestamp_pattern.search(line):
                    found_timestamp = True
                    continue
                if not found_timestamp and line.strip().isdigit():
                    continue
                if found_timestamp and line.strip():
                    # Clean VTT tags
                    clean_line = re.sub(r'<[^>]+>', '', line.strip())
                    if clean_line:
                        text_lines.append(clean_line)
            
            if text_lines:
                full_text = ' '.join(text_lines)
                # Clean up common issues
                full_text = re.sub(r'\s+', ' ', full_text).strip()
                all_segments.append((block_start, block_end, full_text))
        
        if not all_segments:
            print("No subtitle segments found in range.")
            return None
        
        # Merge overlapping/adjacent segments and split into short captions
        # CapCut style: max 6-8 words, short display time
        MAX_WORDS = 7
        MIN_DURATION = 0.8  # Minimum seconds per caption
        MAX_DURATION = 3.0  # Maximum seconds per caption
        
        output_entries = []
        srt_counter = 1
        
        for seg_start, seg_end, text in all_segments:
            # Adjust to clip timeline (offset by start_sec)
            adj_start = max(0, seg_start - start_sec)
            adj_end = min(end_sec - start_sec, seg_end - start_sec)
            
            if adj_end <= adj_start:
                continue
            
            words = text.split()
            total_words = len(words)
            
            if total_words == 0:
                continue
            
            # If short enough, use as-is
            if total_words <= MAX_WORDS:
                entry = {
                    'id': srt_counter,
                    'start': adj_start,
                    'end': adj_end,
                    'text': text
                }
                output_entries.append(entry)
                srt_counter += 1
            else:
                # Split into chunks of MAX_WORDS
                duration = adj_end - adj_start
                num_chunks = (total_words + MAX_WORDS - 1) // MAX_WORDS
                time_per_chunk = duration / num_chunks
                
                for i in range(num_chunks):
                    chunk_words = words[i*MAX_WORDS:(i+1)*MAX_WORDS]
                    chunk_text = ' '.join(chunk_words)
                    
                    chunk_start = adj_start + (i * time_per_chunk)
                    chunk_end = adj_start + ((i + 1) * time_per_chunk)
                    
                    # Ensure minimum duration
                    if chunk_end - chunk_start < MIN_DURATION:
                        chunk_end = chunk_start + MIN_DURATION
                    
                    entry = {
                        'id': srt_counter,
                        'start': chunk_start,
                        'end': min(chunk_end, end_sec - start_sec),
                        'text': chunk_text
                    }
                    output_entries.append(entry)
                    srt_counter += 1
        
        # Remove overlapping entries (keep only one at a time)
        cleaned_entries = []
        for entry in output_entries:
            # Check if this overlaps with previous
            if cleaned_entries:
                prev = cleaned_entries[-1]
                if entry['start'] < prev['end']:
                    # Adjust previous end to prevent overlap
                    prev['end'] = entry['start'] - 0.05
            cleaned_entries.append(entry)
        
        # Write SRT output
        srt_lines = []
        for i, entry in enumerate(cleaned_entries):
            srt_lines.append(str(i + 1))
            srt_lines.append(f"{sec_to_srt_time(entry['start'])} --> {sec_to_srt_time(entry['end'])}")
            srt_lines.append(entry['text'])
            srt_lines.append("")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_lines))
            print(f"CapCut-style subtitle saved: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error writing subtitle: {e}")
            return None

    def _render_dynamic_crop(self, video_path, output_path, edit_list, target_w, target_h, overlay_path=None, subtitle_path=None, subtitle_font="Arial", subtitle_font_size=8, subtitle_font_color="&H00FFFFFF", subtitle_outline_color="&H00000000", subtitle_bg_color="", progress_callback=None):
        """
        Core Helper: Renders video by processing specific segments with dynamic crops and concatenating them.
        Used by: smart_crop_active_speaker_9_16 (switching/cuts) AND smart_crop_9_16 (face tracking re-framing).
        
        edit_list: List of tuples (start, end, crop_x)
        """
        def log(msg):
            if progress_callback: progress_callback(msg)
            print(msg)
            
        try:
            # 1. Render Segments
            temp_clips = []
            log(f"Rendering {len(edit_list)} dynamic segments...")
            
            for idx, (start, end, crop_x) in enumerate(edit_list):
                temp_path = os.path.join(self.output_dir, f"_temp_seg_{idx}.mp4")
                seg_duration = end - start
                
                # Sanity check
                if seg_duration <= 0: continue

                try:
                    input_stream = ffmpeg.input(video_path, ss=start, t=seg_duration)
                    video = input_stream.video.filter('crop', target_w, target_h, crop_x, 0)
                    audio = input_stream.audio
                    
                    (
                        ffmpeg
                        .output(video, audio, temp_path, vcodec=self.video_codec, acodec='aac')
                        .overwrite_output()
                        .run(quiet=True)
                    )
                    if os.path.exists(temp_path):
                        temp_clips.append(temp_path)
                except Exception as e:
                    log(f"Warning: Segment {idx} failed: {e}")

            if not temp_clips:
                log("All segments failed.")
                return None

            # 2. Concat Segments
            log(f"Concatenating {len(temp_clips)} segments...")
            concat_list_path = os.path.join(self.output_dir, "_concat_list.txt")
            with open(concat_list_path, "w", encoding='utf-8') as f:
                for clip in temp_clips:
                    clip_fixed = os.path.abspath(clip).replace("\\", "/")
                    f.write(f"file '{clip_fixed}'\n")

            concat_list_abs = os.path.abspath(concat_list_path).replace("\\", "/")
            
            # First pass: Create raw concatenated video
            raw_output = output_path.replace(".mp4", "_raw.mp4")
            
            try:
                (
                    ffmpeg
                    .input(concat_list_abs, format='concat', safe=0)
                    .output(raw_output, c='copy')
                    .overwrite_output()
                    .run(quiet=False, capture_stderr=True)
                )
            except ffmpeg.Error as e:
                log(f"FFmpeg concat error: {e.stderr.decode('utf-8') if e.stderr else 'Unknown error'}")
                raise

            # 3. Apply Overlay & Subtitles (Re-encode pass)
            has_overlay = overlay_path and os.path.exists(overlay_path)
            has_subtitle = subtitle_path and os.path.exists(subtitle_path)
            
            if has_overlay or has_subtitle:
                log("Applying Overlay/Subtitles...")
                
                input_stream = ffmpeg.input(raw_output)
                video_stream = input_stream.video
                
                if has_overlay:
                    overlay_stream = ffmpeg.input(overlay_path).filter('scale', target_w, target_h)
                    video_stream = ffmpeg.filter([video_stream, overlay_stream], 'overlay', 0, 0)

                if has_subtitle:
                    sub_abs = self._get_ffmpeg_safe_path(subtitle_path)
                    # Build style with custom colors
                    style_parts = [
                        f"Fontname={subtitle_font}",
                        f"FontSize={subtitle_font_size}",
                        f"PrimaryColour={subtitle_font_color}",
                        f"OutlineColour={subtitle_outline_color}",
                        "BorderStyle=1",
                        "Outline=1",
                        "Shadow=0",
                        "Alignment=2",
                        "MarginL=40",
                        "MarginR=40",
                        "MarginV=60",
                        "Bold=0"
                    ]
                    if subtitle_bg_color:
                        # Add background: BorderStyle=4 fills bounding box, allows outline to remain visible
                        style_parts[4] = "BorderStyle=4"  # Replace BorderStyle
                        style_parts.append(f"BackColour={subtitle_bg_color}")
                    style = ','.join(style_parts)
                    video_stream = video_stream.filter('subtitles', sub_abs, force_style=style)

                (
                    ffmpeg
                    .output(video_stream, input_stream.audio, output_path, vcodec=self.video_codec, acodec='aac')
                    .overwrite_output()
                    .run(quiet=False)
                )
                
                # Cleanup raw
                if os.path.exists(raw_output): os.remove(raw_output)
                
            else:
                # No enhancements, just use raw
                if os.path.exists(output_path): os.remove(output_path)
                os.rename(raw_output, output_path)

            # 4. Cleanup Temps
            try: os.remove(concat_list_path)
            except: pass
            for clip in temp_clips:
                try: os.remove(clip)
                except: pass
                
            return output_path

        except Exception as e:
            log(f"Dynamic render failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_face_tracking_path(self, video_path, duration, width, target_w, log_callback=None):
        """
        Analyzes video and generates a simplified 'Camera Path' for re-framing.
        Returns: edit_list [(start, end, crop_x), ...]
        """
        def log(msg):
            if log_callback: log_callback(msg)
            print(msg)
        
        log("Analyzing face movement (Face Tracking)...")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): return None
        
        mp_face_detection = mp.solutions.face_detection
        
        face_x_timeline = [] # (time, center_x)
        
        step_seconds = 0.5
        current_time = 0
        
        with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
            while current_time < duration:
                cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                ret, frame = cap.read()
                if not ret: break
                
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb)
                
                best_x = None
                if results.detections:
                    # Find largest face
                    best_face = max(results.detections, key=lambda d: d.location_data.relative_bounding_box.width * d.location_data.relative_bounding_box.height)
                    bbox = best_face.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    
                    x = int(bbox.xmin * iw)
                    w = int(bbox.width * iw)
                    best_x = x + w // 2
                
                if best_x is not None:
                    face_x_timeline.append((current_time, best_x))
                
                current_time += step_seconds
        
        cap.release()
        
        if not face_x_timeline:
            log("No faces detected for tracking. Using center.")
            return None
            
        # Reframing Logic
        edit_list = []
        
        # Initial position
        current_crop_x = face_x_timeline[0][1] - (target_w // 2)
        
        # Helper clamp
        def clamp_x(val):
            if val < 0: return 0
            if val + target_w > width: return width - target_w
            return val
            
        current_crop_x = clamp_x(current_crop_x)
        segment_start = 0.0
        
        # Threshold for moving camera (don't react to small jitters)
        # 10% of width
        move_threshold = width * 0.10 
        
        for i in range(1, len(face_x_timeline)):
            t, face_x = face_x_timeline[i]
            
            # Ideal crop for this face
            ideal_crop_x = clamp_x(face_x - (target_w // 2))
            
            # Check if we need to move
            if abs(ideal_crop_x - current_crop_x) > move_threshold:
                # SUBJECT MOVED!
                # Close current segment
                segment_end = t
                edit_list.append((segment_start, segment_end, current_crop_x))
                
                # Start new segment
                segment_start = t
                current_crop_x = ideal_crop_x
        
        # Last segment
        edit_list.append((segment_start, duration, current_crop_x))
        
        if len(edit_list) > 1:
             log(f"Generated {len(edit_list)} tracking segments (Subject moved).")
        else:
             log("Subject stationary (Single segment).")
             
        return edit_list

    def smart_crop_9_16(self, video_path, output_path=None, overlay_path=None, subtitle_path=None, subtitle_font="Arial", subtitle_font_size=8, subtitle_font_color="&H00FFFFFF", subtitle_outline_color="&H00000000", subtitle_bg_color="", progress_callback=None):
        """
        Analyzes the video and applies "Smart Crop" with Dynamic Face Tracking.
        Reframing occurs only when the subject moves significantly.
        """
        def log(msg):
            if progress_callback: progress_callback(msg)
            print(msg)

        if not output_path:
            base, ext = os.path.splitext(video_path)
            output_path = f"{base}_9_16{ext}"

        log(f"Processing Smart Crop (Face Tracking) for: {os.path.basename(video_path)}")

        try:
            # 1. Video Info
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print("Could not open video.")
                return None
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / (fps if fps > 0 else 30)
            cap.release()
            
            target_w = int(height * (9 / 16))
            target_h = height
            
            if width < target_w:
                log("Video too narrow. Skipping crop.")
                return video_path

            # 2. Get Tracking Path
            # Returns [(start, end, crop_x), ...]
            edit_list = self._get_face_tracking_path(video_path, duration, width, target_w, log_callback=log)
            
            if not edit_list:
                # Fallback to center
                log("Fallback to center crop.")
                edit_list = [(0, duration, (width - target_w) // 2)]

            # 3. Render using shared helper
            return self._render_dynamic_crop(
                video_path, 
                output_path, 
                edit_list, 
                target_w, 
                target_h, 
                overlay_path=overlay_path, 
                subtitle_path=subtitle_path,
                subtitle_font=subtitle_font,
                subtitle_font_size=subtitle_font_size,
                subtitle_font_color=subtitle_font_color,
                subtitle_outline_color=subtitle_outline_color,
                subtitle_bg_color=subtitle_bg_color,
                progress_callback=progress_callback
            )

        except Exception as e:
            log(f"Smart crop failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def smart_crop_dual_speaker_9_16(self, video_path, output_path=None, overlay_path=None, subtitle_path=None, subtitle_font="Arial", subtitle_font_size=8, subtitle_font_color="&H00FFFFFF", subtitle_outline_color="&H00000000", subtitle_bg_color="", progress_callback=None):
        """
        Analyzes video to detect 2 speakers (Left & Right) and creates split-screen 9:16 format.
        Top half: Left Speaker, Bottom half: Right Speaker.
        """
        def log(msg):
            if progress_callback: progress_callback(msg)
            print(msg)

        if not output_path:
            base, ext = os.path.splitext(video_path)
            # Truncate base name if too long
            if len(os.path.basename(base)) > 60:
                 dir_name = os.path.dirname(base)
                 file_name = os.path.basename(base)[:60] + "..."
                 base = os.path.join(dir_name, file_name)
            output_path = f"{base}_podcast_9_16{ext}"

        log(f"Processing Podcast Mode (Dual Speaker) for: {os.path.basename(video_path)}")
        if overlay_path:
            log(f"Applying overlay: {overlay_path}")
        if subtitle_path:
             log(f"Burning subtitles: {subtitle_path}")

        try:
            # 1. Analyze video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                log("Could not open video for analysis.")
                return None

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / (fps if fps > 0 else 30)
            
            # Target dimensions for each speaker (9:16 aspect ratio, half height output)
            # The final output is 1080x1920 (9:16).
            # So top half is 1080x960. Bottom half is 1080x960.
            # We need to crop a 9:8 ratio from the original video to fit into the half-height slot?
            # Or just crop 9:16 and squeeze? The standard usually is crop 9:16 and scale to half height, 
            # OR crop a 9:16 area and stack them. The previous implementation cropped 9:16 and scaled height to 50%.
            # Let's stick to: Crop 9:16 area centered on face --> Scale to Width x (Height/2).
            # Aspect ratio of 9:16 is 0.5625.
            # If we crop a 9:16 area (e.g. 608x1080) and squash it to 608x540, face looks fat.
            # Better to crop an area that matches the destination aspect ratio (which is half of 9:16 = 9:8 ~ 1.125)
            # But usually podcast shorts just take the 9:16 crop and stack them, meaning the video height is compressed or cropped.
            # Let's simple way: Crop 9:16 area. Then VSTACK.
            # If we VSTACK two 9:16 videos, we get 9:32. That's too tall.
            # We want final result to be 9:16.
            # So Top Speaker = 9:8 ratio? (Square-ish).
            # Yes, 1080 width, 960 height. Ratio = 1.125.
            
            target_single_w = int(height * (9/16)) # Standard 9:16 width
            target_single_h = height
            
            # Actually, to fit 2 speakers in 9:16 frame:
            # Final Frame: W_final, H_final.
            # Top: W_final, H_final/2.
            # So we should crop with aspect ratio (W_final / (H_final/2)) = 2 * (9/16) = 9/8 = 1.125.
            # For 1080p source detection:
            # H_crop = Height.
            # W_crop = H_crop * 1.125.
            # But the source video is 16:9 (1.77). 1.125 fits easily.
            
            # Use 'Scale' approach from before for simplicity, or fix aspect ratio?
            # The user complained about positioning, not aspect ratio distortion.
            # But the previous code did: crop 9:16 -> scale to half height. This makes faces look short/fat!
            # Let's fix this for better quality:
            # Crop a 9:8 region (approx square) for each speaker, so when stacked it forms 9:16.
            
            final_target_w = int(height * (9/16)) # Width of the 9:16 vertical video
            crop_h = height
            crop_w = int(crop_h * (9/16)) # Previous logic used this.
            
            # If we stack two 9:16 crops (scaled to 50% height), we distort.
            # If we stack two 9:16 crops (cropped to 50% height), we lose forehead/chin.
            # Let's try to maintain the previous sizing logic for safety (as User didn't complain about distortion, just centering),
            # BUT improve it if possible.
            # Actually, let's keep the previous valid "Target Width" logic which was 9:16 width relative to height.
            # Checks:
            # target_w = int(height * 9/16)
            # If we crop this W and H, we have a 9:16 video.
            # To put 2 of these into one 9:16 container:
            # Method A: Shrink them 50%. (Distortion if purely scaling Y).
            # Method B: Center crop the middle 50% of the vertical space?
            
            # Given the request is "Left Top, Right Bottom", I will assume standard podcast format:
            # Capture the person in a 9:16 frame might be too narrow if we don't scale.
            # Let's stick to the previous code's geometry to minimize unrelated breakages, just fix the X-centering.
            target_w = int(height * (9/16))
            target_h = height
            
            if width < target_w:
                log("Video too narrow for dual speaker check.")
                cap.release()
                return self.smart_crop_9_16(video_path, output_path=output_path, overlay_path=overlay_path, subtitle_path=subtitle_path, subtitle_font=subtitle_font, subtitle_font_size=subtitle_font_size, subtitle_font_color=subtitle_font_color, subtitle_outline_color=subtitle_outline_color, subtitle_bg_color=subtitle_bg_color, progress_callback=progress_callback)

            # NEW HYBRID LOGIC
            # We want to detect if it's Single or Dual at any point.
            
            # Re-read video to build a timeline
            log("Building Hybrid Timeline (Single vs Dual detection)...")
            cap = cv2.VideoCapture(video_path)
            
            mp_face_detection = mp.solutions.face_detection
            
            # Timeline data: [(time, num_faces, left_x, right_x or center_x)]
            timeline_samples = []
            
            current_time = 0
            step_seconds = 0.5 # Sample rate
            
            with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
                while current_time < duration:
                    cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                    ret, frame = cap.read()
                    if not ret: break
                    
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_detection.process(rgb_frame)
                    
                    faces_found = []
                    if results.detections:
                        ih, iw, _ = frame.shape
                        for detection in results.detections:
                            bbox = detection.location_data.relative_bounding_box
                            cx = int((bbox.xmin + bbox.width/2) * iw)
                            faces_found.append(cx)
                    
                    faces_found.sort()
                    
                    sample_data = {
                        'time': current_time,
                        'count': len(faces_found),
                        'faces': faces_found
                    }
                    timeline_samples.append(sample_data)
                    
                    current_time += step_seconds
            
            cap.release()
            
            # Analyze timeline to create segments
            segments = []
            
            if not timeline_samples:
                log("No faces found in timeline analysis. Using fallback.")
                return self.smart_crop_9_16(video_path, output_path=output_path, overlay_path=overlay_path, subtitle_path=subtitle_path, subtitle_font=subtitle_font, subtitle_font_size=subtitle_font_size, subtitle_font_color=subtitle_font_color, subtitle_outline_color=subtitle_outline_color, subtitle_bg_color=subtitle_bg_color, progress_callback=progress_callback)

            # Smoothing: We don't want to switch every 0.5s.
            # Logic: Group consecutive samples of same type.
            # Note: "Same type" means 1 face vs >=2 faces.
            
            # Initial state
            curr_type = 'DUAL' if timeline_samples[0]['count'] >= 2 else 'SINGLE'
            curr_start = 0.0
            
            # Data accumulation for the segment (to find average positions)
            curr_data_samples = [timeline_samples[0]]
            
            min_segment_duration = 1.2 # Minimum duration to hold a shot style (reduced for responsiveness)
            
            midpoint = width // 2

            for i in range(1, len(timeline_samples)):
                sample = timeline_samples[i]
                sample_type = 'DUAL' if sample['count'] >= 2 else 'SINGLE'
                
                # If type changed
                if sample_type != curr_type:
                    # Check if previous segment was long enough? 
                    # For now, just commit and maybe merge later? 
                    # Let's commit.
                    
                    # Calculate segment data
                    # Determine stable crop positions for this segment
                    seg_data = {}
                    if curr_type == 'SINGLE':
                        # Find median center
                        centers = []
                        for s in curr_data_samples:
                             if s['faces']:
                                 # Use the largest face? Or strictly the only face?
                                 # If single mode but multiple faces appeared briefly (noise), pick one.
                                 # Usually we pick center-most or largest.
                                 # Let's pick median of all faces seen.
                                 centers.extend(s['faces'])
                        
                        if centers:
                            seg_data['center_x'] = int(np.median(centers))
                        else:
                            seg_data['center_x'] = width // 2
                            
                    else: # DUAL
                        # Find median Left and median Right
                        lefts = []
                        rights = []
                        for s in curr_data_samples:
                            if len(s['faces']) >= 2:
                                # Assuming sorted: [0] is left, [-1] is right
                                lefts.append(s['faces'][0])
                                rights.append(s['faces'][-1])
                            elif len(s['faces']) == 1:
                                # Anomalous single frame in dual segment
                                pass
                        
                        if lefts: seg_data['left_x'] = int(np.median(lefts))
                        else: seg_data['left_x'] = width // 4
                        
                        if rights: seg_data['right_x'] = int(np.median(rights))
                        else: seg_data['right_x'] = (width * 3) // 4
                    
                    segments.append({
                        'type': curr_type,
                        'start': curr_start,
                        'end': sample['time'],
                        'data': seg_data
                    })
                    
                    # Reset
                    curr_type = sample_type
                    curr_start = sample['time']
                    curr_data_samples = [sample]
                else:
                    curr_data_samples.append(sample)
                    
            # Add last segment
            seg_data = {}
            if curr_type == 'SINGLE':
                centers = []
                for s in curr_data_samples:
                    if s['faces']: centers.extend(s['faces'])
                seg_data['center_x'] = int(np.median(centers)) if centers else width // 2
            else:
                lefts = []
                rights = []
                for s in curr_data_samples:
                    if len(s['faces']) >= 2:
                        lefts.append(s['faces'][0])
                        rights.append(s['faces'][-1])
                seg_data['left_x'] = int(np.median(lefts)) if lefts else width // 4
                seg_data['right_x'] = int(np.median(rights)) if rights else (width * 3) // 4
                
            segments.append({
                'type': curr_type,
                'start': curr_start,
                'end': duration,
                'data': seg_data
            })
            
            # Optimize segments (Merge short jitters)
            # Logic: If a segment is < min_segment_duration, merge it into the previous segment.
            # If it's the very first segment, we merge into the next one (deferred).
            
            optimized_segments = []
            if segments:
                current_seg = segments[0]
                
                for i in range(1, len(segments)):
                    next_seg = segments[i]
                    
                    seg_duration = current_seg['end'] - current_seg['start']
                    
                    # Check if current segment is too short (and not the only one)
                    if seg_duration < min_segment_duration:
                        # Merge into next_seg? Or merge next_seg into this? 
                        # Usually we want to "extend the previous state". 
                        # But here 'current_seg' IS the 'previous state' relative to 'next_seg'.
                        # Wait. If 'current_seg' is short, it means the state change that created it was fleeting.
                        # So we should probably have merged it into *its* predecessor.
                        # But we are iterating forward.
                        
                        # Approach:
                        # If optimized_segments is not empty, merge current unstable segment into the LAST stable segment.
                        if optimized_segments:
                            last_stable = optimized_segments[-1]
                            # Extend last stable segment to cover this short segment
                            last_stable['end'] = current_seg['end'] 
                            # 'current_seg' is now effectively consumed.
                            # The 'next_seg' becomes the new candidate for 'current_seg'
                            current_seg = next_seg
                        else:
                            # It's the first segment and it's short.
                            # We can't merge back. We must merge forward.
                            # We make 'next_seg' start where 'current_seg' started.
                            # And the type will be 'next_seg's type (so we basically skip the first short bit)
                            next_seg['start'] = current_seg['start']
                            current_seg = next_seg
                    else:
                        # Current segment is stable enough. Keep it.
                        optimized_segments.append(current_seg)
                        current_seg = next_seg
                
                # Handle the final trailing segment
                final_duration = current_seg['end'] - current_seg['start']
                if final_duration < min_segment_duration and optimized_segments:
                    # Merge into previous
                    optimized_segments[-1]['end'] = current_seg['end']
                else:
                    optimized_segments.append(current_seg)
            
            log(f"Smoothed segments: {len(segments)} -> {len(optimized_segments)}")

            return self._render_hybrid_crop(
                video_path,
                output_path,
                optimized_segments,
                target_w,
                target_h,
                overlay_path=overlay_path,
                subtitle_path=subtitle_path,
                subtitle_font=subtitle_font,
                subtitle_font_size=subtitle_font_size,
                subtitle_font_color=subtitle_font_color,
                subtitle_outline_color=subtitle_outline_color,
                subtitle_bg_color=subtitle_bg_color,
                progress_callback=progress_callback
            )

        except Exception as e:
            log(f"Hybrid mode failed: {e}")
            import traceback
            traceback.print_exc()
            return self.smart_crop_9_16(video_path, output_path=output_path, overlay_path=overlay_path, subtitle_path=subtitle_path, subtitle_font=subtitle_font, subtitle_font_size=subtitle_font_size, subtitle_font_color=subtitle_font_color, subtitle_outline_color=subtitle_outline_color, subtitle_bg_color=subtitle_bg_color, progress_callback=progress_callback)
            
        except Exception as e:
            log(f"Dual speaker crop failed: {e}")
            import traceback
            traceback.print_exc()
            return self.smart_crop_9_16(video_path, output_path=output_path, overlay_path=overlay_path, subtitle_path=subtitle_path, subtitle_font=subtitle_font, subtitle_font_size=subtitle_font_size, subtitle_font_color=subtitle_font_color, subtitle_outline_color=subtitle_outline_color, subtitle_bg_color=subtitle_bg_color, progress_callback=progress_callback)

    def smart_crop_active_speaker_9_16(self, video_path, output_path=None, overlay_path=None, subtitle_path=None, subtitle_font="Arial", subtitle_font_size=8, subtitle_font_color="&H00FFFFFF", subtitle_outline_color="&H00000000", subtitle_bg_color="", progress_callback=None):
        """
        Active Speaker Mode: Dynamically cuts between 2 speakers based on who is talking.
        Uses Faster-Whisper for speech timestamps and MediaPipe for mouth movement detection.
        """
        from audio_transcriber import AudioTranscriber
        
        def log(msg):
            if progress_callback: progress_callback(msg)
            print(msg)

        if not output_path:
            base, ext = os.path.splitext(video_path)
            # Truncate base name if too long to avoid Windows MAX_PATH (limit to ~60 chars for base)
            # Full path limit is 260. We leave room for directory path + suffix.
            if len(os.path.basename(base)) > 60:
                 dir_name = os.path.dirname(base)
                 file_name = os.path.basename(base)[:60] + "..."
                 base = os.path.join(dir_name, file_name)
                 
            output_path = f"{base}_active_speaker{ext}"

        log(f"Active Speaker Mode for: {os.path.basename(video_path)}")

        try:
            # 1. Get video info
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                log("Could not open video.")
                return None

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / (fps if fps > 0 else 30)
            cap.release()

            # Target 9:16 dimensions
            target_w = int(height * (9 / 16))
            target_h = height

            if width < target_w:
                log("Video too narrow for 9:16. Skipping.")
                return video_path

            midpoint = width // 2

            # 2. Extract audio and transcribe for speech timestamps
            log("Extracting audio for transcription...")
            audio_path = self.extract_audio(video_path)
            if not audio_path:
                log("Audio extraction failed. Falling back to static crop.")
                return self.smart_crop_9_16(video_path, output_path=output_path, overlay_path=overlay_path, subtitle_path=subtitle_path, subtitle_font=subtitle_font, subtitle_font_size=subtitle_font_size, subtitle_font_color=subtitle_font_color, subtitle_outline_color=subtitle_outline_color, subtitle_bg_color=subtitle_bg_color, progress_callback=progress_callback)

            log("Transcribing with Faster-Whisper...")
            transcriber = AudioTranscriber(model_size="base", device="cpu", compute_type="int8")
            speech_segments = transcriber.transcribe(audio_path, language="id")

            # Cleanup audio file
            try: os.remove(audio_path)
            except: pass

            if not speech_segments:
                log("No speech detected. Falling back to static crop.")
                return self.smart_crop_9_16(video_path, output_path=output_path, overlay_path=overlay_path, subtitle_path=subtitle_path, subtitle_font=subtitle_font, subtitle_font_size=subtitle_font_size, subtitle_font_color=subtitle_font_color, subtitle_outline_color=subtitle_outline_color, subtitle_bg_color=subtitle_bg_color, progress_callback=progress_callback)

            log(f"Found {len(speech_segments)} speech segments.")

            # 3. Detect faces and identify Left/Right speaker positions (initial scan)
            log("Analyzing face positions...")
            cap = cv2.VideoCapture(video_path)
            mp_face_detection = mp.solutions.face_detection
            mp_face_mesh = mp.solutions.face_mesh

            left_face_xs = []
            right_face_xs = []

            with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
                sample_times = [duration * i / 10 for i in range(1, 10)]  # Sample at 10%, 20%, ...90%
                for t in sample_times:
                    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
                    ret, frame = cap.read()
                    if not ret:
                        continue

                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_detection.process(rgb)

                    if results.detections:
                        for det in results.detections:
                            bbox = det.location_data.relative_bounding_box
                            x = int(bbox.xmin * width)
                            w = int(bbox.width * width)
                            center_x = x + w // 2

                            if center_x < midpoint:
                                left_face_xs.append(center_x)
                            else:
                                right_face_xs.append(center_x)

            cap.release()

            if not left_face_xs or not right_face_xs:
                log("Could not detect 2 distinct speakers. Falling back to static crop.")
                return self.smart_crop_9_16(video_path, output_path=output_path, overlay_path=overlay_path, subtitle_path=subtitle_path, subtitle_font=subtitle_font, subtitle_font_size=subtitle_font_size, subtitle_font_color=subtitle_font_color, subtitle_outline_color=subtitle_outline_color, subtitle_bg_color=subtitle_bg_color, progress_callback=progress_callback)

            left_center = int(np.median(left_face_xs))
            right_center = int(np.median(right_face_xs))
            log(f"Speaker positions: Left={left_center}, Right={right_center}")

            # Crop X for each speaker
            def calc_crop_x(center_x):
                cx = center_x - (target_w // 2)
                if cx < 0: cx = 0
                if cx + target_w > width: cx = width - target_w
                return cx

            left_crop_x = calc_crop_x(left_center)
            right_crop_x = calc_crop_x(right_center)

            # 4. For each speech segment, determine active speaker via Mouth Aspect Ratio (MAR)
            log("Analyzing mouth movement for each speech segment...")
            cap = cv2.VideoCapture(video_path)

            # Mouth landmarks for MAR calculation (lip corners and vertical points)
            # Using indices: 13 (top lip), 14 (bottom lip), 78 (left corner), 308 (right corner)
            UPPER_LIP = 13
            LOWER_LIP = 14
            LEFT_CORNER = 78
            RIGHT_CORNER = 308

            def get_mar(landmarks, ih, iw):
                """Calculate Mouth Aspect Ratio"""
                try:
                    upper = landmarks[UPPER_LIP]
                    lower = landmarks[LOWER_LIP]
                    left = landmarks[LEFT_CORNER]
                    right = landmarks[RIGHT_CORNER]

                    vertical = abs((upper.y - lower.y) * ih)
                    horizontal = abs((right.x - left.x) * iw)

                    if horizontal < 1:
                        return 0
                    return vertical / horizontal
                except:
                    return 0

            edit_list = []  # [(start_sec, end_sec, crop_x), ...]

            with mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=2, min_detection_confidence=0.5) as face_mesh:
                for seg in speech_segments:
                    seg_start = seg["start"]
                    seg_end = seg["end"]
                    seg_mid = (seg_start + seg_end) / 2

                    # Sample frames in this segment
                    sample_count = min(5, int((seg_end - seg_start) * 2))  # ~2 samples per second
                    if sample_count < 1:
                        sample_count = 1

                    left_mars = []
                    right_mars = []
                    
                    # Store center X positions for this specific segment to handle movement
                    left_segment_xs = []
                    right_segment_xs = []

                    for i in range(sample_count):
                        t = seg_start + (seg_end - seg_start) * (i + 1) / (sample_count + 1)
                        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
                        ret, frame = cap.read()
                        if not ret:
                            continue

                        ih, iw, _ = frame.shape
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = face_mesh.process(rgb)

                        if results.multi_face_landmarks:
                            for face_landmarks in results.multi_face_landmarks:
                                lm = face_landmarks.landmark
                                # Determine if this face is Left or Right based on nose position
                                nose_x = lm[1].x * iw  # Nose tip
                                
                                # Calculate rough face center from landmarks (average of boundaries)
                                mesh_xs = [l.x * iw for l in lm]
                                mesh_center_x = sum(mesh_xs) / len(mesh_xs)

                                mar = get_mar(lm, ih, iw)

                                if nose_x < midpoint:
                                    left_mars.append(mar)
                                    left_segment_xs.append(mesh_center_x)
                                else:
                                    right_mars.append(mar)
                                    right_segment_xs.append(mesh_center_x)

                    # Determine active speaker: higher average MAR = more mouth movement = speaker
                    avg_left = np.mean(left_mars) if left_mars else 0
                    avg_right = np.mean(right_mars) if right_mars else 0

                    if avg_left > avg_right and avg_left > 0.03:
                        # Use segment-specific center if available, else global
                        if left_segment_xs:
                            seg_center = int(np.mean(left_segment_xs))
                            active_crop_x = calc_crop_x(seg_center)
                        else:
                            active_crop_x = left_crop_x # Global fallback
                        active_label = "LEFT"
                        
                    elif avg_right > avg_left and avg_right > 0.03:
                        # Use segment-specific center if available, else global
                        if right_segment_xs:
                            seg_center = int(np.mean(right_segment_xs))
                            active_crop_x = calc_crop_x(seg_center)
                        else:
                            active_crop_x = right_crop_x # Global fallback
                        active_label = "RIGHT"
                        
                    else:
                        # No clear speaker - use center or last known
                        active_crop_x = (left_crop_x + right_crop_x) // 2
                        active_label = "CENTER"

                    edit_list.append((seg_start, seg_end, active_crop_x))
                    log(f"  [{seg_start:.1f}s-{seg_end:.1f}s] {active_label} (L:{avg_left:.3f}, R:{avg_right:.3f})")

            cap.release()

            if not edit_list:
                log("No edit points generated. Falling back.")
                return self.smart_crop_9_16(video_path, output_path=output_path, overlay_path=overlay_path, subtitle_path=subtitle_path, subtitle_font=subtitle_font, subtitle_font_size=subtitle_font_size, subtitle_font_color=subtitle_font_color, subtitle_outline_color=subtitle_outline_color, subtitle_bg_color=subtitle_bg_color, progress_callback=progress_callback)

            # 5. Generate FFmpeg sendcmd script for dynamic cropping
            log("Generating dynamic crop commands...")

            # Merge adjacent segments with same crop_x to reduce commands
            # [Stabilization Update] Merge if crop_x is SIMILAR (within threshold) to prevent jitter.
            # Also fills small silence gaps between segments for smoother viewing.
            merged_edits = []
            stabilization_threshold = width * 0.05 # 5% tolerance (e.g. ~50-100px)

            for start, end, crop_x in edit_list:
                if merged_edits:
                    last_start, last_end, last_x = merged_edits[-1]
                    
                    # Check if same speaker position (approx)
                    if abs(last_x - crop_x) < stabilization_threshold:
                        # STABILIZE: Use the previous camera position (last_x) to prevent mini-jumps
                        # EXTEND: Update end time to current segment's end. 
                        # This effectively fills the gap between segments with the static shot.
                        merged_edits[-1] = (last_start, end, last_x)
                    else:
                        merged_edits.append((start, end, crop_x))
                else:
                    merged_edits.append((start, end, crop_x))

            # Generate sendcmd format
            # Format: time crop_x crop_y
            cmd_lines = []
            for start, end, crop_x in merged_edits:
                cmd_lines.append(f"{start:.3f} crop x {crop_x}")

            # Write to temp file
            cmd_file = os.path.join(self.output_dir, "_active_speaker_cmds.txt")
            with open(cmd_file, "w") as f:
                f.write("\n".join(cmd_lines))

            # 6. Render using shared helper
            return self._render_dynamic_crop(
                video_path,
                output_path,
                merged_edits,
                target_w,
                target_h,
                overlay_path=overlay_path,
                subtitle_path=subtitle_path,
                subtitle_font=subtitle_font,
                subtitle_font_size=subtitle_font_size,
                subtitle_font_color=subtitle_font_color,
                subtitle_outline_color=subtitle_outline_color,
                subtitle_bg_color=subtitle_bg_color,
                progress_callback=progress_callback
            )

        except Exception as e:
            log(f"Active Speaker processing failed: {e}")
            import traceback
            traceback.print_exc()
            return self.smart_crop_9_16(video_path, output_path=output_path, overlay_path=overlay_path, subtitle_path=subtitle_path, subtitle_font=subtitle_font, subtitle_font_size=subtitle_font_size, subtitle_font_color=subtitle_font_color, subtitle_outline_color=subtitle_outline_color, subtitle_bg_color=subtitle_bg_color, progress_callback=progress_callback)

    def _render_hybrid_crop(self, video_path, output_path, timeline_segments, target_w, target_h, overlay_path=None, subtitle_path=None, subtitle_font="Arial", subtitle_font_size=8, subtitle_font_color="&H00FFFFFF", subtitle_outline_color="&H00000000", subtitle_bg_color="", progress_callback=None):
        """
        Renders hybrid video (Single/Split mixed) based on segments.
        timeline_segments: List of dicts: {'type': 'SINGLE'/'DUAL', 'start': float, 'end': float, 'data': ...}
        """
        def log(msg):
            if progress_callback: progress_callback(msg)
            print(msg)

        try:
            temp_clips = []
            log(f"Rendering {len(timeline_segments)} hybrid segments...")

            width = 0 # To detect if we need re-reading
            
            # Helper to get video dimensions once
            if not width:
                probe = ffmpeg.probe(video_path)
                video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
                width = int(video_info['width'])
                height = int(video_info['height'])

            # Ensure even targets to please the encoder gods (h264 requires mod 2)
            target_w = (target_w // 2) * 2
            target_h = (target_h // 2) * 2

            for idx, seg in enumerate(timeline_segments):
                seg_type = seg['type']
                start = seg['start']
                end = seg['end']
                duration = end - start
                
                if duration <= 0: continue

                temp_path = os.path.join(self.output_dir, f"_temp_hybrid_{idx}.mp4")
                
                try:
                    input_stream = ffmpeg.input(video_path, ss=start, t=duration)
                    
                    if seg_type == 'SINGLE':
                        # Crop 9:16 centered on 'center_x'
                        center_x = seg['data']['center_x']
                        crop_x = center_x - (target_w // 2)
                        # Clamp
                        if crop_x < 0: crop_x = 0
                        if crop_x + target_w > width: crop_x = width - target_w
                        
                        video = input_stream.video.filter('crop', target_w, target_h, crop_x, 0)
                        
                    elif seg_type == 'DUAL':
                        # Split screen
                        lx = seg['data']['left_x']
                        rx = seg['data']['right_x']
                        
                        # Use 9:8 crop strategy for high quality stacking
                        target_w_9_8 = int(height * 1.125)
                        # Ensure even
                        target_w_9_8 = (target_w_9_8 // 2) * 2
                        
                        if width >= target_w_9_8:
                            # Quality Mode
                            real_w = target_w_9_8
                            real_h = height
                            
                            c_x1 = int(lx - (real_w // 2))
                            if c_x1 < 0: c_x1 = 0
                            if c_x1 + real_w > width: c_x1 = width - real_w
                            
                            c_x2 = int(rx - (real_w // 2))
                            if c_x2 < 0: c_x2 = 0
                            if c_x2 + real_w > width: c_x2 = width - real_w
                            
                            top = input_stream.video.filter('crop', real_w, real_h, c_x1, 0)
                            btm = input_stream.video.filter('crop', real_w, real_h, c_x2, 0)
                            
                            stacked = ffmpeg.filter([top, btm], 'vstack')
                            video = stacked.filter('scale', target_w, target_h)
                            
                        else:
                            # Fallback Mode (Squash)
                            c_x1 = int(lx - (target_w // 2))
                            if c_x1 < 0: c_x1 = 0
                            if c_x1 + target_w > width: c_x1 = width - target_w
                            
                            c_x2 = int(rx - (target_w // 2))
                            if c_x2 < 0: c_x2 = 0
                            if c_x2 + target_w > width: c_x2 = width - target_w

                            v1 = input_stream.video.filter('crop', target_w, target_h, c_x1, 0).filter('scale', target_w, target_h // 2)
                            v2 = input_stream.video.filter('crop', target_w, target_h, c_x2, 0).filter('scale', target_w, target_h // 2)
                            video = ffmpeg.filter([v1, v2], 'vstack')

                    # Encode segment
                    (
                        ffmpeg
                        .output(video, input_stream.audio, temp_path, vcodec=self.video_codec, acodec='aac')
                        .overwrite_output()
                        .run(quiet=True)
                    )
                    
                    if os.path.exists(temp_path):
                        temp_clips.append(temp_path)
                        
                except ffmpeg.Error as e:
                    log(f"Warning: Hybrid Segment {idx} failed: {e}")
                    if e.stderr:
                         log(f"FFmpeg stderr: {e.stderr.decode('utf8', errors='ignore')}")
                except Exception as e:
                    log(f"Warning: Hybrid Segment {idx} failed (Generic): {e}")

            if not temp_clips:
                log("All hybrid segments failed.")
                return None

            # Concat
            log(f"Concatenating {len(temp_clips)} hybrid segments...")
            concat_list_path = os.path.join(self.output_dir, "_hybrid_list.txt")
            with open(concat_list_path, "w", encoding='utf-8') as f:
                for clip in temp_clips:
                    clip_fixed = os.path.abspath(clip).replace("\\", "/")
                    f.write(f"file '{clip_fixed}'\n")

            concat_list_abs = os.path.abspath(concat_list_path).replace("\\", "/")
            raw_output = output_path.replace(".mp4", "_raw.mp4")

            (
                ffmpeg
                .input(concat_list_abs, format='concat', safe=0)
                .output(raw_output, c='copy')
                .overwrite_output()
                .run(quiet=True)
            )

            # Apply Overlay/Subtitles (Re-encode pass)
            # This logic mimics _render_dynamic_crop but for the hybrid result
            has_overlay = overlay_path and os.path.exists(overlay_path)
            has_subtitle = subtitle_path and os.path.exists(subtitle_path)
            
            if has_overlay or has_subtitle:
                log("Applying Overlay/Subtitles to Hybrid Video...")
                input_stream = ffmpeg.input(raw_output)
                video_stream = input_stream.video
                
                if has_overlay:
                    overlay_stream = ffmpeg.input(overlay_path).filter('scale', target_w, target_h)
                    video_stream = ffmpeg.filter([video_stream, overlay_stream], 'overlay', 0, 0)

                if has_subtitle:
                    sub_abs = self._get_ffmpeg_safe_path(subtitle_path)
                    # Build style with custom colors
                    style_parts = [
                        f"Fontname={subtitle_font}",
                        f"FontSize={subtitle_font_size}",
                        f"PrimaryColour={subtitle_font_color}",
                        f"OutlineColour={subtitle_outline_color}",
                        "BorderStyle=1",
                        "Outline=1",
                        "Shadow=0",
                        "Alignment=2",
                        "MarginL=40",
                        "MarginR=40",
                        "MarginV=60",
                        "Bold=0"
                    ]
                    if subtitle_bg_color:
                        # Add background: BorderStyle=4 fills bounding box, allows outline to remain visible
                        style_parts[4] = "BorderStyle=4"  # Replace BorderStyle
                        style_parts.append(f"BackColour={subtitle_bg_color}")
                    style = ','.join(style_parts)
                    video_stream = video_stream.filter('subtitles', sub_abs, force_style=style)

                (
                    ffmpeg
                    .output(video_stream, input_stream.audio, output_path, vcodec=self.video_codec, acodec='aac')
                    .overwrite_output()
                    .run(quiet=False)
                )
                if os.path.exists(raw_output): os.remove(raw_output)
            else:
                if os.path.exists(output_path): os.remove(output_path)
                os.rename(raw_output, output_path)

            # Cleanup
            try: os.remove(concat_list_path)
            except: pass
            for clip in temp_clips:
                try: os.remove(clip)
                except: pass

            return output_path

        except Exception as e:
            log(f"Hybrid render failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def optimize_for_platform(self, video_path, platform, output_path=None, progress_callback=None):
        """
        Optimize video for specific social media platform
        
        Args:
            video_path: Input video path
            platform: Target platform name (e.g., "TikTok", "YouTube Shorts")
            output_path: Output path (optional)
            progress_callback: Progress callback function
            
        Returns:
            str: Path to optimized video, or None if failed
        """
        try:
            # Get platform specifications
            spec = PlatformOptimizer.get_platform_spec(platform)
            
            if not output_path:
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                platform_safe = platform.replace(" ", "_").replace("/", "_")
                output_path = os.path.join(self.output_dir, f"{base_name}_{platform_safe}_optimized.mp4")
            
            print(f"Optimizing video for {platform}...")
            if progress_callback:
                progress_callback(f"Optimizing for {platform}...")
            
            # Get video info
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            audio_info = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            
            current_width = int(video_info['width'])
            current_height = int(video_info['height'])
            duration = float(probe['format']['duration'])
            
            # Platform specifications
            target_width, target_height = spec['resolution']
            target_fps = spec['fps']
            video_bitrate = spec['bitrate']
            audio_bitrate = spec['audio_bitrate']
            
            # Check duration warnings
            duration_warnings = PlatformOptimizer.validate_duration(platform, duration)
            for warning in duration_warnings:
                print(f"⚠️ {warning}")
            
            # Calculate optimal crop/scale
            current_ratio = current_width / current_height
            target_ratio = target_width / target_height
            
            input_stream = ffmpeg.input(video_path)
            
            # Video processing
            if abs(current_ratio - target_ratio) < 0.01:
                # Same aspect ratio, just scale
                video = input_stream.video.filter('scale', target_width, target_height)
                print(f"Scaling from {current_width}x{current_height} to {target_width}x{target_height}")
            elif current_ratio > target_ratio:
                # Source is wider, crop horizontally
                scale_height = target_height
                scale_width = int(current_width * (target_height / current_height))
                crop_x = (scale_width - target_width) // 2
                
                video = (input_stream.video
                        .filter('scale', scale_width, scale_height)
                        .filter('crop', target_width, target_height, crop_x, 0))
                print(f"Crop horizontal: {current_width}x{current_height} -> {scale_width}x{scale_height} -> {target_width}x{target_height}")
            else:
                # Source is taller, crop vertically  
                scale_width = target_width
                scale_height = int(current_height * (target_width / current_width))
                crop_y = (scale_height - target_height) // 2
                
                video = (input_stream.video
                        .filter('scale', scale_width, scale_height)
                        .filter('crop', target_width, target_height, 0, crop_y))
                print(f"Crop vertical: {current_width}x{current_height} -> {scale_width}x{scale_height} -> {target_width}x{target_height}")
            
            # Apply frame rate if different
            current_fps = eval(video_info.get('r_frame_rate', '30/1'))
            if abs(current_fps - target_fps) > 0.1:
                video = video.filter('fps', fps=target_fps)
                print(f"Frame rate: {current_fps:.1f} -> {target_fps}")
            
            # Audio processing
            if audio_info:
                audio = input_stream.audio
            else:
                # Create silent audio if no audio track
                audio = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=48000', f='lavfi').audio
            
            # Output with platform-specific settings
            output_args = {
                'vcodec': self.video_codec,
                'acodec': 'aac',
                'video_bitrate': video_bitrate,
                'audio_bitrate': audio_bitrate,
                'movflags': '+faststart',  # Web optimization
            }
            
            # Hardware encoding specific settings
            if self.video_codec == "h264_nvenc":
                output_args.update({
                    'preset': 'fast',
                    'profile:v': 'high',
                    'level': '4.1',
                    'rc': 'cbr'
                })
            elif self.video_codec == "libx264":
                output_args.update({
                    'preset': 'fast',
                    'profile:v': 'high',
                    'level': '4.1',
                    'crf': '23'
                })
            
            # Add progress tracking
            def progress_handler(percentage):
                if progress_callback:
                    progress_callback(f"Optimizing for {platform}: {percentage:.1f}%")
            
            out = ffmpeg.output(video, audio, output_path, **output_args)
            out = ffmpeg.overwrite_output(out)
            
            # Run with progress tracking
            process = ffmpeg.run_async(out, pipe_stderr=True)
            
            while True:
                output = process.stderr.readline()
                if output == b'' and process.poll() is not None:
                    break
                if output:
                    line = output.decode('utf-8').strip()
                    if 'time=' in line and 'speed=' in line:
                        try:
                            time_part = line.split('time=')[1].split(' ')[0]
                            h, m, s = time_part.split(':')
                            current_time = int(h) * 3600 + int(m) * 60 + float(s)
                            percentage = min((current_time / duration) * 100, 99)
                            progress_handler(percentage)
                        except:
                            pass
            
            return_code = process.poll()
            if return_code == 0:
                if progress_callback:
                    progress_callback(f"✅ Platform optimization complete for {platform}")
                print(f"✅ Successfully optimized for {platform}: {output_path}")
                
                # Show optimization summary
                new_size = os.path.getsize(output_path) / (1024*1024)  # MB
                print(f"📊 Optimization Summary:")
                print(f"   Platform: {spec['description']}")
                print(f"   Resolution: {target_width}x{target_height}")
                print(f"   Duration: {duration:.1f}s")
                print(f"   File Size: {new_size:.1f} MB")
                for warning in duration_warnings:
                    print(f"   ⚠️ {warning}")
                
                return output_path
            else:
                raise Exception(f"FFmpeg failed with return code {return_code}")
                
        except Exception as e:
            error_msg = f"Platform optimization failed: {e}"
            print(error_msg)
            if progress_callback:
                progress_callback(f"❌ {error_msg}")
            return None

    def batch_optimize_platforms(self, video_path, platforms, output_dir=None, progress_callback=None):
        """
        Optimize video for multiple platforms at once
        
        Args:
            video_path: Input video path
            platforms: List of platform names
            output_dir: Custom output directory (optional)
            progress_callback: Progress callback function
            
        Returns:
            dict: Platform name -> output path mapping
        """
        results = {}
        total_platforms = len(platforms)
        
        if not output_dir:
            output_dir = self.output_dir
        
        for i, platform in enumerate(platforms):
            def platform_progress(msg):
                overall_progress = f"[{i+1}/{total_platforms}] {msg}"
                if progress_callback:
                    progress_callback(overall_progress)
                print(overall_progress)
            
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            platform_safe = platform.replace(" ", "_").replace("/", "_")
            output_path = os.path.join(output_dir, f"{base_name}_{platform_safe}.mp4")
            
            result = self.optimize_for_platform(video_path, platform, output_path, platform_progress)
            results[platform] = result
            
            if result:
                platform_progress(f"✅ {platform} optimization complete")
            else:
                platform_progress(f"❌ {platform} optimization failed")
        
        return results

