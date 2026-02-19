import mss
import time
import threading
import os
from datetime import datetime
from PIL import Image

class ScreenRecorder:
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.is_recording = False
        self.is_saving = False
        self.thread = None
        self.output_path = ""
        self.on_save_complete = None

    def start_recording(self, monitor_index=1, region=None):
        if self.is_recording or self.is_saving:
            return None
        
        self.is_recording = True
        self.output_path = self._get_record_path()
        
        if region:
            monitor = {"top": region[1], "left": region[0], "width": region[2], "height": region[3]}
        else:
            with mss.mss() as sct:
                if monitor_index >= len(sct.monitors):
                    monitor_index = 0
                monitor = sct.monitors[monitor_index]
            
        self.thread = threading.Thread(target=self._record_loop, args=(monitor,), daemon=True)
        self.thread.start()
        return self.output_path

    def _get_record_path(self):
        today = datetime.now().strftime("%Y-%m-%d")
        day_dir = os.path.join(self.file_manager.config["save_dir"], today)
        if not os.path.exists(day_dir):
            os.makedirs(day_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%H-%M-%S")
        fmt = self.file_manager.config.get("rec_format", "gif").lower()
        return os.path.join(day_dir, f"record_{timestamp}.{fmt}")

    def _record_loop(self, monitor):
        fps = 10.0
        frame_delay = 1.0 / fps
        raw_frames = []
        
        with mss.mss() as sct:
            while self.is_recording:
                start_time = time.time()
                try:
                    sct_img = sct.grab(monitor)
                    raw_frames.append((sct_img.bgra, sct_img.size))
                    if len(raw_frames) >= 600: # Increased to 1 min @ 10fps
                        self.is_recording = False
                        break
                except Exception as e:
                    print(f"Capture Error: {e}")
                    break
                
                elapsed = time.time() - start_time
                if elapsed < frame_delay:
                    time.sleep(frame_delay - elapsed)
        
        if raw_frames:
            self.is_saving = True
            save_thread = threading.Thread(target=self._process_and_save, args=(raw_frames, frame_delay), daemon=True)
            save_thread.start()
        else:
            self.is_saving = False

    def _process_and_save(self, raw_frames, frame_delay):
        import subprocess
        try:
            processed_frames = []
            for bgra, size in raw_frames:
                img = Image.frombytes("RGB", size, bgra, "raw", "BGRX")
                if img.width > 1920: # Higher res for MP4
                    img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
                processed_frames.append(img)

            if not processed_frames: return

            if self.output_path.lower().endswith(".gif"):
                processed_frames[0].save(
                    self.output_path,
                    save_all=True,
                    append_images=processed_frames[1:],
                    optimize=True,
                    duration=int(frame_delay * 1000),
                    loop=0
                )
            else:
                # MP4 via FFmpeg
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Save frames as temporary PNGs
                    for i, frame in enumerate(processed_frames):
                        frame.save(os.path.join(tmpdir, f"f_{i:04d}.png"))
                    
                    # Call FFmpeg
                    cmd = [
                        'ffmpeg', '-y',
                        '-framerate', str(1.0/frame_delay),
                        '-i', os.path.join(tmpdir, 'f_%04d.png'),
                        '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p',
                        '-crf', '23',
                        self.output_path
                    ]
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        except Exception as e:
            print(f"Process/Save Error: {e}")
        finally:
            self.is_saving = False
            if self.on_save_complete:
                self.on_save_complete(self.output_path)

    def stop_recording(self, callback=None):
        self.is_recording = False
        self.on_save_complete = callback
        return self.output_path
