import json
import os
import time
from datetime import datetime
import uuid
import random

class SessionState:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.history = ""
        self.current_seed = -1
        self.char_desc = ""
        self.style = ""
        self.images = []
        self.scene_texts = []
        self.num_scenes = 3

    def reset(self):
        self.session_id = str(uuid.uuid4())
        self.history = ""
        self.current_seed = random.randint(0, 1000000)
        self.char_desc = ""
        self.style = ""
        self.images = []
        self.scene_texts = []
        self.num_scenes = 3
        return self

class SessionManager:
    def __init__(self, storage_path="sessions"):
        self.storage_path = storage_path
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def save_session(self, session_id, history, character, style, seed, num_scenes):
        """
        Saves the current session state to a JSON file.
        """
        data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "character": character,
            "style": style,
            "seed": seed,
            "num_scenes": num_scenes,
            "history": history
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
