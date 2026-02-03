import torch
from diffusers import StableDiffusionPipeline
from PIL import Image, ImageDraw
import hashlib

class ImageGenerator:
    def __init__(self, device=None, low_memory_mode=False):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.low_memory_mode = low_memory_mode
        print(f"Using device: {self.device}, Low memory mode: {low_memory_mode}")
        self.pipeline = None
        # Use the official v1-5 repo which is more reliable
        self.model_id = "stable-diffusion-v1-5/stable-diffusion-v1-5"
        self.last_error = None

    def load_model(self):
        """Loads the Stable Diffusion model."""
        if self.pipeline is not None:
            return

        print(f"Loading Stable Diffusion model ({self.model_id})...")
        try:
            # Memory optimizations
            if self.low_memory_mode:
                print("Using low memory optimizations...")
                # Use basic memory optimizations
                pipeline_kwargs = {
                    "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                }
            else:
                pipeline_kwargs = {
                    "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                }

            self.pipeline = StableDiffusionPipeline.from_pretrained(
                self.model_id,
                safety_checker=None,
                requires_safety_checker=False,
                use_safetensors=True,
                **pipeline_kwargs
            )

            if self.device == "cuda":
                self.pipeline.enable_attention_slicing()
                if self.low_memory_mode:
                    # Enable model CPU offloading for CUDA with low memory
                    try:
                        self.pipeline.enable_model_cpu_offload()
                        print("Model CPU offloading enabled")
                    except Exception as e:
                        print(f"CPU offloading failed: {e}")
                else:
                    self.pipeline.to(self.device)
            else:
                # CPU optimizations
                self.pipeline.enable_attention_slicing()
                if self.low_memory_mode:
                    # Enable sequential CPU offload for very low memory
                    try:
                        self.pipeline.enable_sequential_cpu_offload()
                        print("Sequential CPU offload enabled")
                    except Exception as e:
                        print(f"Sequential CPU offload failed: {e}")
                else:
                    # Standard CPU loading
                    pass
                
            print("Model loaded successfully.")
            self.last_error = None
        except Exception as e:
            error_msg = str(e)
            print(f"Failed to load model: {error_msg}")
            self.last_error = error_msg
            self.pipeline = None

    def generate(self, prompt, negative_prompt="", seed=None, height=512, width=512, steps=30, educational_mode=False):
        """Generates an image from a prompt."""
        if self.pipeline is None:
            # Try loading again if it wasn't loaded
            self.load_model()
            if self.pipeline is None:
                return self.create_dummy_image(prompt)

        # Adjust resolution for low memory mode
        if self.low_memory_mode:
            height = min(height, 384)
            width = min(width, 384)
            print(f"Low memory mode: using {width}x{height} resolution")

        # Default strong negative prompt for educational mode
        if educational_mode and not negative_prompt:
            negative_prompt = (
                "blurry, low quality, deformed, ugly, bad anatomy, extra limbs, poorly drawn face, bad proportions, "
                "extra fingers, fused fingers, malformed hands, watermark, text, signature, logo, username, "
                "cartoon, anime, 3d render, painting, sketch, lowres, jpeg artifacts, noise, grain, overexposed, "
                "underexposed, bad lighting, chromatic aberration, lens flare, unrealistic, fantasy, surreal, "
                "colorful background, abstract art, artistic, decorative"
            )

        # If seed is provided, we use it for consistency.
        # If seed is -1 or None, we randomize.
        if seed is None or seed == -1:
            seed = torch.randint(0, 1000000, (1,)).item()
        
        print(f"Generating with seed: {seed}")
        generator = torch.Generator(device=self.device).manual_seed(seed)

        try:
            # Adjust steps and guidance for educational mode
            if educational_mode:
                actual_steps = 25 if self.device == "cuda" else 15
                guidance_scale = 9.0
            else:
                actual_steps = steps if self.device == "cuda" else 15
                guidance_scale = 7.5
            
            # autocast for mixed precision
            if self.device == 'cuda':
                with torch.autocast(self.device):
                    image = self._run_pipeline(prompt, negative_prompt, height, width, actual_steps, generator, guidance_scale)
            else:
                image = self._run_pipeline(prompt, negative_prompt, height, width, actual_steps, generator, guidance_scale)
            
            # Add frame for educational mode
            if educational_mode:
                image = self.add_frame(image)
            
            return image
        except Exception as e:
            self.last_error = str(e)
            print(f"Error during generation: {e}")
            return self.create_dummy_image(prompt)

    def _run_pipeline(self, prompt, negative_prompt, height, width, steps, generator, guidance_scale=7.5):
        return self.pipeline(
            prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
            height=height,
            width=width
        ).images[0]

    def add_frame(self, image):
        """Adds a simple frame to the image for educational purposes."""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        draw.rectangle([(10, 10), (width-10, height-10)], outline="black", width=4)
        return image

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
