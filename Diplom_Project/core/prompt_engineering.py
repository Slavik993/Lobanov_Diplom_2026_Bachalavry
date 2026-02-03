import random

class PromptEngineer:
    def __init__(self):
        self.styles = {
            "Cinematic": "cinematic lighting, dramatic atmosphere, detailed texture, 8k, unreal engine 5 render, ray tracing",
            "Anime": "anime style, makoto shinkai style, studio ghibli, vibrant colors, detailed background, cel shaded",
            "Oil Painting": "oil painting, textured, impressionist, van gogh style, heavy strokes",
            "Cyberpunk": "cyberpunk, neon lights, night city, rain, futuristic, sci-fi, detailed techno",
            "Educational": (
                "clean white background, simple flat illustration, infographic style, clear lines, "
                "minimalist diagram, vector art, high contrast, legible, educational diagram, textbook style, "
                "no shadows, no gradients, schematic, explanatory illustration, 4k resolution"
            ),
            "Scheme": (
                "technical scheme, blueprint style, black and white line art, precise, labeled diagram, "
                "flowchart elements, arrows, boxes, clear text placeholders, engineering drawing"
            ),
            "Presentation Slide": (
                "powerpoint slide style, clean layout, large text placeholders, minimalistic, corporate design, "
                "white background, blue accents, professional, high readability"
            ),
            "Algorithm Flowchart": (
                "technical flowchart diagram, algorithm visualization, programming logic flow, "
                "decision diamonds, process rectangles, arrows, data flow, pseudocode blocks, "
                "computational steps, software engineering diagram, code structure, logic gates, "
                "boolean operations, sorting algorithm steps, array elements, comparison operations, "
                "swap operations, loop structures, conditional statements, educational technical diagram, "
                "computer science diagram, programming tutorial illustration, clean line art, "
                "monochrome technical drawing, precise geometric shapes, labeled flowchart elements"
            ),
            "Database Schema": (
                "database ER diagram, entity relationship model, database tables, primary keys, foreign keys, "
                "relationships, cardinality, crow's foot notation, SQL schema, data modeling, "
                "relational database design, database architecture, clean technical diagram"
            ),
            "Neural Network": (
                "neural network architecture diagram, artificial intelligence, machine learning model, "
                "layers, neurons, connections, weights, activation functions, deep learning, "
                "computational graph, AI model structure, data flow, technical neural diagram"
            ),
            "Web Interface": (
                "web UI wireframe, user interface design, website layout, responsive design, "
                "user experience, navigation menu, content blocks, forms, buttons, "
                "web development mockup, digital interface, clean web design diagram"
            ),
            "Code Structure": (
                "software architecture diagram, class diagram, object oriented design, "
                "UML diagram, inheritance, polymorphism, encapsulation, design patterns, "
                "code structure, module dependencies, software engineering, clean technical diagram"
            )
        }
        self.camera_angles = [
            "wide angle shot", "close up", "eye level", "low angle", "hero shot", "panoramic view"
        ]
        self.lighting = [
            "natural lighting", "studio lighting", "soft creative lighting", "volumetric lighting", "rembrandt lighting"
        ]
        
        # Negative prompts for different styles to avoid unwanted elements
        self.negative_prompts = {
            "Algorithm Flowchart": "photorealistic, 3d, shadows, gradients, colors, people, faces, animals, nature, artistic, decorative, blurry, low quality, distorted, games, violence, horror, blood, weapons, monsters, fantasy, sci-fi, action, adventure, cartoon, anime, manga, video games, board games, puzzles, entertainment",
            "Database Schema": "photorealistic, 3d, shadows, gradients, colors, people, faces, animals, nature, artistic, decorative, blurry, low quality, distorted, rounded corners, icons, games, violence, horror, fantasy, sci-fi, action, adventure, cartoon, anime, manga",
            "Neural Network": "photorealistic, 3d, shadows, gradients, colors, people, faces, animals, nature, artistic, decorative, blurry, low quality, distorted, text, labels, games, violence, horror, fantasy, sci-fi, action, adventure, cartoon, anime, manga, organic, biological",
            "Web Interface": "photorealistic, 3d, shadows, gradients, people, faces, animals, nature, artistic, decorative, blurry, low quality, distorted, handwritten, organic shapes, games, violence, horror, fantasy, sci-fi, action, adventure, cartoon, anime, manga",
            "Code Structure": "photorealistic, 3d, shadows, gradients, colors, people, faces, animals, nature, artistic, decorative, blurry, low quality, distorted, rounded corners, games, violence, horror, fantasy, sci-fi, action, adventure, cartoon, anime, manga",
            "Educational": "photorealistic, 3d, shadows, gradients, people, faces, animals, nature, artistic, decorative, blurry, low quality, distorted, colors, textures, games, violence, horror, fantasy, sci-fi, action, adventure, cartoon, anime, manga",
            "Scheme": "photorealistic, 3d, shadows, gradients, colors, people, faces, animals, nature, artistic, decorative, blurry, low quality, distorted, games, violence, horror, fantasy, sci-fi, action, adventure, cartoon, anime, manga",
            "Presentation Slide": "photorealistic, 3d, shadows, gradients, people, faces, animals, nature, artistic, decorative, blurry, low quality, distorted, handwritten, games, violence, horror, fantasy, sci-fi, action, adventure, cartoon, anime, manga"
        }

    def build_prompt(self, base_description, style_name="Cinematic", character_desc="", add_random_camera=False, educational_mode=False):
        """
        Constructs a complex prompt based on multiple parameters.
        Returns tuple: (positive_prompt, negative_prompt)
        """
        components = []

        # 1. Base Logic: Subject (Character + Action)
        if character_desc:
            components.append(f"{character_desc}, {base_description}")
        else:
            components.append(base_description)

        # 2. Style Injection
        style_prompt = self.styles.get(style_name, self.styles["Cinematic"])
        components.append(style_prompt)

        # 3. Educational/IT-specific enhancements
        if educational_mode:
            components.append("simple illustration:1.3, clean background:1.4, high contrast:1.2, legible text:1.3")
            
            # Additional IT-specific enhancements for technical styles
            it_styles = ["Algorithm Flowchart", "Database Schema", "Neural Network", "Web Interface", "Code Structure"]
            if style_name in it_styles:
                components.append("technical accuracy:1.4, precise geometry:1.3, professional diagram:1.2, engineering standard:1.2")

        # 4. Camera (Optional)
        if add_random_camera:
            components.append(random.choice(self.camera_angles))

        # 5. Lighting (Randomized for variety but keeping high quality)
        if not educational_mode:  # Skip lighting for educational to keep clean
            components.append(random.choice(self.lighting))

        # 6. Quality Boosters
        components.append("high quality, masterpiece, sharp focus")

        positive_prompt = ", ".join(components)
        
        # Get negative prompt for the style
        negative_prompt = self.negative_prompts.get(style_name, "blurry, low quality, distorted, ugly, deformed")

        return positive_prompt, negative_prompt

    def get_available_styles(self):
        return list(self.styles.keys())
