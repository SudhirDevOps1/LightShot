import os
import json
from datetime import datetime

class FileManager:
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = os.path.join(os.path.expanduser("~"), "Screenshots")
        else:
            self.base_dir = base_dir
        
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.history_path = os.path.join(self.base_dir, "history.json")
        self._ensure_dir(self.base_dir)
        self.config = self._load_config()

    def _ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def _load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return json.load(f)
        return {
            "save_dir": self.base_dir,
            "format": "png",
            "quality": 95,
            "watermark_text": "",
            "enable_watermark": False,
            "rec_format": "gif"
        }

    def save_config(self, config):
        self.config.update(config)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def get_save_path(self):
        today = datetime.now().strftime("%Y-%m-%d")
        day_dir = os.path.join(self.config["save_dir"], today)
        self._ensure_dir(day_dir)
        
        timestamp = datetime.now().strftime("%H-%M-%S")
        filename = f"screenshot_{timestamp}.{self.config['format']}"
        return os.path.join(day_dir, filename)

    def save_screenshot(self, image, path=None):
        if path is None:
            path = self.get_save_path()
        
        image.save(path, format=self.config["format"].upper(), quality=self.config["quality"])
        self._add_to_history(path)
        return path

    def _add_to_history(self, file_path):
        history = []
        if os.path.exists(self.history_path):
            with open(self.history_path, "r") as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []
        
        entry = {
            "path": file_path,
            "timestamp": datetime.now().isoformat(),
            "filename": os.path.basename(file_path)
        }
        history.append(entry)
        
        with open(self.history_path, "w") as f:
            json.dump(history, f, indent=4)

    def get_history(self):
        if os.path.exists(self.history_path):
            with open(self.history_path, "r") as f:
                return json.load(f)
        return []
