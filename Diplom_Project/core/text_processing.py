import random

class TextProcessor:
    def __init__(self):
        self.enhancements = [
            "high quality, detailed, digital art",
            "beautiful, cinematic, trending on artstation",
            "sharp focus, studio lighting, ultra detailed",
            "vibrant colors, masterpiece",
            "concept art, 8k resolution"
        ]

    def split_story_into_scenes(self, story_text, num_scenes=4):
        """Splits the story text into a specified number of scenes."""
        # Normalize text: remove extra spaces and split by dots
        story_text = ' '.join(story_text.strip().split())
        sentences = [s.strip() + '.' for s in story_text.split('.') if s.strip()]

        if not sentences:
            return ["Empty scene."] * num_scenes

        # If fewer sentences than scenes, extend
        while len(sentences) < num_scenes:
            sentences.append(sentences[-1])

        # Distribute sentences across scenes
        scenes = []
        # Simple distribution: if we have more sentences than scenes, merge some
        # If we have mostly equal, just map 1 to 1 logic or similar.
        
        # Here we use a simple approach: verify we have at least 'num_scenes' items
        # If we have many sentences, we chunk them.
        
        chunk_size = len(sentences) / num_scenes
        for i in range(num_scenes):
            start = int(i * chunk_size)
            end = int((i + 1) * chunk_size) if i < num_scenes - 1 else len(sentences)
            scene_text = " ".join(sentences[start:end])
            if not scene_text: # Fallback if math goes slightly off or empty chunk
                 scene_text = sentences[min(start, len(sentences)-1)]
            scenes.append(scene_text)

        return scenes

    def enhance_prompt(self, scene_text, style_prefix=""):
        """Enhances the prompt with style keywords."""
        # If we have a style prefix, use it.
        # Ideally, we don't want RANDOM enhancements for a comic where consistency matters.
        # But for now, let's keep it simple or allow a fixed enhancement if provided.
        if not style_prefix and not any(x in scene_text for x in ["artstation", "detailed"]):
             enhancement = random.choice(self.enhancements)
             return f"{scene_text}, {enhancement}".strip()
        
        return f"{style_prefix} {scene_text}".strip()

    def extract_visual_part(self, text):
        """
        Extracts the part of the text that describes the scene visually, 
        ignoring dialogue if possible or summarizing.
        For a simple MVP: We assume the generator output might contain 
        mixed dialogue and description. We'll try to use the whole text 
        but maybe truncate or focus on non-dialogue lines if marked.
        """
        # Simple heuristic: remove quotes? Or just pass it all.
        # Let's clean up quotes to avoid text bubble confusion in the model 
        # (though SD usually ignores text meaning, dialogue can confuse the scene composition).
        
        # Remove text inside quotes (Dialogue)
        import re
        # Remove "Page X" or "chapter" headers if any
        clean_text = re.sub(r'"[^"]*"', '', text) 
        
        # If we removed everything (only dialogue), revert to original text
        if len(clean_text) < 10:
            return text
            
        return clean_text.strip()
