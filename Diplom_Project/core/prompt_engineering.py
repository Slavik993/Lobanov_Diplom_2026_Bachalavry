import random

class PromptEngineer:
    def __init__(self):
        self.styles = {
            "Cinematic": "cinematic lighting, dramatic atmosphere, detailed texture, 8k, unreal engine 5 render, ray tracing",
            "Anime": "anime style, makoto shinkai style, studio ghibli, vibrant colors, detailed background, cel shaded",
            "Oil Painting": "oil painting, textured, impressionist, van gogh style, heavy strokes",
            "Cyberpunk": "cyberpunk, neon lights, night city, rain, futuristic, sci-fi, detailed techno"
        }
        self.camera_angles = [
            "wide angle shot", "close up", "eye level", "low angle", "hero shot", "panoramic view"
        ]
        self.lighting = [
            "natural lighting", "studio lighting", "soft creative lighting", "volumetric lighting", "rembrandt lighting"
        ]

    def build_prompt(self, base_description, style_name="Cinematic", character_desc="", add_random_camera=False, story_context=""):
        """
        Constructs a complex prompt based on multiple parameters.
        """
        components = []

        # 1. Base Logic: Subject (Character + Action)
        if character_desc:
            components.append(f"{character_desc}, {base_description}")
        else:
            components.append(base_description)

        # Add story context for coherence
        if story_context:
            components.append(f"Story context: {story_context}")

        # 2. Style Injection
        style_prompt = self.styles.get(style_name, self.styles["Cinematic"])
        components.append(style_prompt)

        # 3. Camera (Optional)
        if add_random_camera:
            components.append(random.choice(self.camera_angles))

        # 4. Lighting (Randomized for variety but keeping high quality)
        components.append(random.choice(self.lighting))

        # 5. Quality Boosters
        components.append("high quality, masterpiece, sharp focus, highly detailed, intricate details, photorealistic, professional digital art")

        return ", ".join(components)

    def get_available_styles(self):
        return list(self.styles.keys())
