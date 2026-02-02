import torch
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
from PIL import Image, ImageDraw
import hashlib

class ImageGenerator:
    def __init__(self, device=None):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        self.pipeline = None
        # Use Stable Diffusion XL for better quality
        self.model_id = "stabilityai/stable-diffusion-xl-base-1.0"
        self.last_error = None

    def load_model(self):
        """Loads the Stable Diffusion model."""
        if self.pipeline is not None:
            return

        print(f"Loading Stable Diffusion model ({self.model_id})...")
        try:
            self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                use_safetensors=True
            ).to(self.device)

            # Use DPM++ 2M Karras scheduler for better quality
            self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(self.pipeline.scheduler.config, use_karras_sigmas=True)

            if self.device == "cuda":
                self.pipeline.enable_attention_slicing()
            else:
                # CPU optimizations
                # self.pipeline.enable_sequential_cpu_offload() # Can save memory but slower
                pass
                
            print("Model loaded successfully.")
            self.last_error = None
        except Exception as e:
            error_msg = str(e)
            print(f"Failed to load model: {error_msg}")
            self.last_error = error_msg
            self.pipeline = None

    def generate(self, prompt, negative_prompt="", seed=None, height=1024, width=1024, steps=30):
        """Generates an image from a prompt."""
        if self.pipeline is None:
            # Try loading again if it wasn't loaded
            self.load_model()
            if self.pipeline is None:
                return self.create_dummy_image(prompt)

        # If seed is provided, we use it for consistency.
        # If seed is -1 or None, we randomize.
        if seed is None or seed == -1:
            seed = torch.randint(0, 1000000, (1,)).item()
        
        print(f"Generating with seed: {seed}")
        generator = torch.Generator(device=self.device).manual_seed(seed)

        try:
            # Reduce steps for CPU to make it faster to test
            actual_steps = steps if self.device == "cuda" else 15
            
            # autocast for mixed precision
            if self.device == 'cuda':
                with torch.autocast(self.device):
                    image = self._run_pipeline(prompt, negative_prompt, height, width, actual_steps, generator)
            else:
                image = self._run_pipeline(prompt, negative_prompt, height, width, actual_steps, generator)
            
            return image
        except Exception as e:
            self.last_error = str(e)
            print(f"Error during generation: {e}")
            return self.create_dummy_image(prompt)

    def _run_pipeline(self, prompt, negative_prompt, height, width, steps, generator):
        return self.pipeline(
            prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=9.0,
            generator=generator,
            height=height,
            width=width
        ).images[0]

    def create_dummy_image(self, prompt):
        """Creates a placeholder image if the model fails or isn't loaded."""
        hash_val = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
        r = (hash_val % 256)
        g = ((hash_val // 256) % 256)
        b = ((hash_val // 65536) % 256)

        img = Image.new('RGB', (512, 512), color=(r, g, b))
        draw = ImageDraw.Draw(img)
        
        # Draw a pattern
        for i in range(0, 512, 10):
            draw.line([(i, 0), (512-i, 512)], fill=(255, 255, 255), width=2)
            
        error_text = f"Error: {self.last_error}" if self.last_error else "Model Error"
        # Simple text wrapping or truncation
        draw.text((20, 20), error_text[:80], fill=(255, 0, 0))
        if len(error_text) > 80:
             draw.text((20, 35), error_text[80:160], fill=(255, 0, 0))
             
        draw.text((20, 60), "Prompt: " + prompt[:50], fill=(255, 255, 255))
        return img
