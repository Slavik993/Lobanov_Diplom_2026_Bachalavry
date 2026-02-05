import json
import os
import time
from datetime import datetime

class SessionManager:
    def __init__(self, storage_path="sessions"):
        self.storage_path = storage_path
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def save_session(self, session_id, history, character, style, seed, educational_mode=False, images=None, chat_history=None):
        """
        Saves the current session state and images to a timestamped folder.
        Structure: outputs/session_{id}/{timestamp}/
        """
        # Create structured path
        # Timestamp format: YYYY-MM-DD_HH-MM-SS
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Base outputs directory
        base_outputs_dir = os.path.join(os.path.dirname(self.storage_path), "outputs")
        
        # Session directory
        session_dir = os.path.join(base_outputs_dir, f"session_{session_id}")
        
        # Sequence directory (timestamped)
        sequence_dir = os.path.join(session_dir, timestamp_str)
        
        if not os.path.exists(sequence_dir):
            os.makedirs(sequence_dir)

        image_paths = []
        if images:
            for idx, img in enumerate(images):
                img_filename = f"img_{idx}.png"
                img_path = os.path.join(sequence_dir, img_filename)
                try:
                    img.save(img_path)
                    image_paths.append(img_path)
                    print(f"Saved image to {img_path}")
                except Exception as e:
                    print(f"Failed to save image {img_filename}: {e}")

        data = {
            "session_id": session_id,
            "timestamp": timestamp_str,
            "character": character,
            "style": style,
            "seed": seed,
            "educational_mode": educational_mode,
            "history": history,
            "chat_history": chat_history or [], # Save structured list
            "saved_images": image_paths
        }
        
        # Save JSON in the same timestamped folder
        json_filename = "session_metadata.json"
        json_filepath = os.path.join(sequence_dir, json_filename)
        
        # Also save a reference in the main sessions folder for quick access if needed, 
        # or just rely on this new structure. User asked for specific folders.
        # Let's keep the main sessions pointer simple for now, maybe updated with latest path.
        
        try:
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Session saved to {json_filepath}")
            return json_filepath
        except Exception as e:
            print(f"Failed to save session: {e}")
            return None

    def import_session_file(self, file_path):
        """
        Imports session data from a specific JSON file.
        """
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to import session from {file_path}: {e}")
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
