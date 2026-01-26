import json
import os

class Config:
    DEFAULT_CONFIG = {
        "app_name": "StoryForge Lite",
        "version": "1.0.0",
        "model": {
            "text_generator": "distilgpt2",
            "image_generator": "stable-diffusion-v1-5/stable-diffusion-v1-5",
            "device_priority": "cuda"
        },
        "generation": {
            "default_steps": 25,
            "default_height": 512,
            "default_width": 512,
            "guidance_scale": 7.5
        },
        "paths": {
            "output_dir": "outputs",
            "sessions_dir": "sessions",
            "logs_dir": "logs"
        }
    }

    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.data = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """Loads configuration from file if it exists."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._update_recursive(self.data, user_config)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        """Saves current configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def _update_recursive(self, d, u):
        """Recursively updates a dictionary."""
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._update_recursive(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def get(self, key, default=None):
        """Retrieves a config value using dot notation (e.g., 'model.text_generator')."""
        keys = key.split('.')
        val = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

# Global instance
config = Config()
