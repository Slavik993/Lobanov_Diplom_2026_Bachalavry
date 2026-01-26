import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from core.generator import ImageGenerator

print("Initializing ImageGenerator...")
generator = ImageGenerator()

print("Loading model...")
generator.load_model()

if generator.pipeline:
    print("Model loaded successfully!")
    print("Testing generation...")
    img = generator.generate("A majestic mountain")
    if generator.last_error:
        print(f"Generation failed: {generator.last_error}")
    else:
        print("Generation successful!")
        img.save("test_output.png")
        print("Saved to test_output.png")
else:
    print(f"Model failed to load. Last error: {generator.last_error}")
