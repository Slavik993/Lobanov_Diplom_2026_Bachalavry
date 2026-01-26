import os
import datetime
import json

class Storage:
    def __init__(self, base_dir="outputs"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def save_session(self, story_text, scenes, prompts, images):
        """Saves values of the current generation session."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.base_dir, f"story_{timestamp}")
        
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)

        # Save metadata
        metadata = {
            "original_story": story_text,
            "scenes": scenes,
            "prompts": prompts,
            "timestamp": timestamp
        }
        
        with open(os.path.join(session_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)

        # Save images
        saved_paths = []
        for i, img in enumerate(images):
            filename = f"scene_{i+1:02d}.png"
            path = os.path.join(session_dir, filename)
            img.save(path)
            saved_paths.append(path)
            
        return session_dir
