import random

class PromptEngineer:
    def __init__(self):
        self.styles = {
            "Cinematic": (
                "movie scene, detailed environment, dramatic lighting, shot on 35mm, "
                "shallow depth of field, sharp focus, hyperrealistic, dynamic composition, "
                "color graded, unreal engine 5 render, ray tracing"
            ),
            "Anime": "anime style, makoto shinkai style, studio ghibli, vibrant colors, detailed background, cel shaded",
            "Oil Painting": "oil painting, textured, impressionist, van gogh style, heavy strokes",
            "Cyberpunk": "cyberpunk, neon lights, night city, rain, futuristic, sci-fi, detailed techno",
            "Educational": (
                "clean white background, simple flat illustration, infographic style, clear lines, "
                "minimalist diagram, vector art, high contrast, legible, educational diagram, textbook style, "
                "no shadows, no gradients, schematic, explanatory illustration, 4k resolution, minimal colors"
            ),
            "Comic Book": (
                "comic book style, graphic novel visualization, bold ink lines, vibrant colors, "
                "dynamic composition, expressive characters, sequential art, detailed background, "
                "high quality digital art, masterpiece, 8k resolution"
            ),
            "Algorithm Flowchart": (
                "clean flow chart diagram on white background, 2d vector graphics, black lines, "
                "process rectangles and decision diamonds, straight connecting arrows, "
                "miminalist technical drawing, no shading, high contrast, academic diagram style"
            ),
            "Database Schema": (
                "entity relationship diagram on white background, crow's foot notation, "
                "rectangular tables with attribute lists, clear connecting lines, "
                "black and white technical drawing, vector style, flat design, database structure"
            ),
            "Neural Network": (
                "schematic neural network diagram on white background, input hidden and output layers, "
                "nodes as simple circles, straight connecting lines, 2d flat vector graphics, "
                "scientific illustration style, no visual noise, clear structure"
            ),
            "Data Analysis": (
                "data visualization dashboard on white background, statistical charts, "
                "clean histograms and scatter plots, heatmap matrix with clear grid, "
                "vector graphics, flat design, 2-3 accent colors (blue, orange), academic presentation style"
            ),
            "Web Architecture": (
                "web application architecture diagram on white background, client server database blocks, "
                "linear data flow arrows, flat 2d vector icons, clean structural scheme, "
                "minimalist technical illustration, high contrast, system design"
            ),
            "User Interface": (
                "wireframe UI design on white background, grayscale low-fidelity mockup, "
                "placeholder blocks for header nav and content, clean outlines, "
                "UX schematic, skeletal layout, no photorealism"
            ),
            "Code Structure": (
                "UML class diagram on white background, rectangular class blocks, "
                "inheritance arrows, clear hierarchy, black and white line art, "
                "software engineering schematic, vector graphics"
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
        
        # 0. Global Visual Anchor (Enforce consistency across sequence)
        # We derive a visual anchor from the character description (Topic) and style
        visual_anchor = "unified design language, coherent color palette (blue and white)"
        if style_name == "Data Analysis":
            visual_anchor = "unified academic dashboard style, bright orange accents, clean grid layout"
        elif style_name == "Neural Network":
            visual_anchor = "unified scientific schematic style, teal and grey accents, circuit motifs"
        elif "Algorithm" in style_name:
            visual_anchor = "unified technical document style, black outlines, minimal yellow highlighting"

        # 1. Base Logic: Subject (Topic + Specific Step Variation)
        # Ensure the TOPIC (character_desc) is always present if needed, but context-aware
        if character_desc:
            # Check if we are in an IT/Educational flow where "mechanism" makes sense
            if style_name in ["Algorithm Flowchart", "Database Schema", "Neural Network", "Web Architecture", "Code Structure", "Data Analysis"]:
                components.append(f"{character_desc} mechanism: {base_description}")
            
            # For Comic Book / Stories, we want to establish context but focus on the specific scene
            elif style_name == "Comic Book":
                 # If character_desc is very long (whole story), we shouldn't use it all as a prefix.
                 # Assuming app.py might pass a shorter context or we truncate it.
                 # Better strategy: rely on base_description being the scene, and add a generic style anchor.
                 # But we need the "Knight" context. 
                 # Let's assume character_desc is the full story. We can't easily extract just the knight.
                 # We'll use a generic "Context" prefix or rely on the split text being self-contained enough
                 # IF we updated app.py to split smarter. 
                 # For now, let's treat character_desc as the "Title/Theme" if it's short, or ignore if it's the duplicate of base_desc
                 if len(character_desc) < 100:
                    components.append(f"Story about {character_desc}: {base_description}")
                 else:
                    # If it's a long story, the base_description (scene) is likely enough if extracted well,
                    # OR we simply don't prefix to avoid confusion, trusting the scene text.
                    components.append(base_description)
            else:
                # Default fallback
                components.append(f"{character_desc}, {base_description}")
        else:
            components.append(base_description)

        # 2. Style Injection
        style_prompt = self.styles.get(style_name, self.styles["Cinematic"])
        components.append(style_prompt)
        
        # 3. Add Visual Anchor
        # For Comic Book, we need a strong style anchor
        if style_name == "Comic Book":
             components.append("consistent character design, sequential panel art, unified graphic novel style")
             # Comic Book needs different quality anchors than educational
        elif educational_mode:
            components.append(visual_anchor)

        # 4. Educational/IT-specific enhancements
        # Only apply cleaning if NOT Comic Book. Comic Book needs different handling.
        if educational_mode and style_name != "Comic Book":
            components.append("simple illustration:1.3, clean background:1.4, high contrast:1.2, legible text:1.3")
            
            # Additional IT-specific enhancements for technical styles
            it_styles = ["Algorithm Flowchart", "Database Schema", "Neural Network", "Web Architecture", "User Interface", "Data Analysis", "Code Structure"]
            if style_name in it_styles:
                components.append("technical accuracy:1.4, precise geometry:1.3, professional diagram:1.2, engineering standard:1.2")
                components.append("no background noise, vector lines, flat style, 2d, minimalist")

        # 5. Camera (Optional)
        if add_random_camera and not educational_mode and style_name != "Comic Book":
            components.append(random.choice(self.camera_angles))

        # 6. Lighting (Randomized for variety but keeping high quality)
        if not educational_mode and style_name != "Comic Book":  # Skip lighting for educational to keep clean
            components.append(random.choice(self.lighting))
        elif style_name == "Comic Book":
            components.append("dramatic lighting, cinematic shading, ambient light")

        # 7. Quality Boosters
        components.append("high quality, masterpiece, sharp focus")

        positive_prompt = ", ".join(components)
        
        # Get negative prompt for the style
        negative_prompt = self.negative_prompts.get(style_name, "blurry, low quality, distorted, ugly, deformed")
        if educational_mode and style_name != "Comic Book":
             # Add extra negative prompts for text/messiness if in educational mode
             negative_prompt += ", artistic, painterly, grunge, dirty, complex background, photo, realistic, 3d render"
             
        if style_name == "Comic Book":
             # Specific negatives for comics
             negative_prompt += ", photo, realistic, 3d, b&w, sketch, minimalist, simple, boring"

        return positive_prompt, negative_prompt

    def get_available_styles(self):
        return list(self.styles.keys())
