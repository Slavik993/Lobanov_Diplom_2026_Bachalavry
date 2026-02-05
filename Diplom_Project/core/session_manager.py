import json
import os
import time
from datetime import datetime

class SessionManager:
    def __init__(self, storage_path="sessions"):
        self.storage_path = storage_path
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def save_session(self, session_id, history, character, style, seed, educational_mode=False, images=None):
        """
        Saves the current session state to a JSON file and images to the outputs directory.
        """
        # Ensure outputs directory exists
        outputs_dir = os.path.join(os.path.dirname(self.storage_path), "outputs")
        if not os.path.exists(outputs_dir):
            os.makedirs(outputs_dir)

        image_paths = []
        if images:
            for idx, img in enumerate(images):
                img_filename = f"{session_id}_img_{idx}.png"
                img_path = os.path.join(outputs_dir, img_filename)
                try:
                    img.save(img_path)
                    image_paths.append(img_path)
                    print(f"Saved image to {img_path}")
                except Exception as e:
                    print(f"Failed to save image {img_filename}: {e}")

        data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "character": character,
            "style": style,
            "seed": seed,
            "educational_mode": educational_mode,
            "history": history,
            "saved_images": image_paths
        }
        
        filename = f"session_{session_id}.json"
        filepath = os.path.join(self.storage_path, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Session saved to {filepath}")
            return filepath
        except Exception as e:
            print(f"Failed to save session: {e}")
            return None

    def load_session(self, session_id):
        """
        Loads a session by ID.
        """
        filename = f"session_{session_id}.json"
        filepath = os.path.join(self.storage_path, filename)
        
        if not os.path.exists(filepath):
            return None
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load session: {e}")
            return None

    def list_sessions(self):
        """
        Returns a list of all saved session files.
        """
        try:
            files = [f for f in os.listdir(self.storage_path) if f.startswith("session_") and f.endswith(".json")]
            return sorted(files, reverse=True)
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
