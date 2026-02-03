from transformers import pipeline, set_seed
import torch

class StoryTeller:
    def __init__(self, model_name="ai-forever/rugpt3small_based_on_gpt2", device="cpu"):
        self.device = device
        print(f"Loading StoryTeller model ({model_name}) on {self.device}...")
        try:
            # Explicitly set device=-1 for CPU in pipeline, or 0 for CUDA
            # device_id = -1 if device == "cpu" else 0  <- Pipeline handles device strings well usually, but let's be safe
            device_id = -1 if device == "cpu" else 0
            self.generator = pipeline('text-generation', model=model_name, device=device_id)
            print("StoryTeller model loaded.")
        except Exception as e:
            print(f"Failed to load StoryTeller model: {e}")
            self.generator = None

    def generate_response(self, context, user_input, educational_mode=False, max_length=150):
        """
        Generates the next part of the story based on context and user input.
        """
        if not self.generator:
            return "Ведущий: (Модель молчит. Проверьте подключение.)"

        # Construct prompt - Using Russian prompts
        # We assume 'context' is mostly empty or clean from previous turns.
        # Ideally, we keep a running context.
        
        # Simplified prompt construction for RuGPT
        # Custom prompt for educational mode
        if educational_mode or (isinstance(context, str) and "Лектор:" in context):
             # Try to keep it strict
             prompt = f"{context}\nСтудент: {user_input}\nЛектор:"
        else:
             prompt = f"{context}\nИгрок: {user_input}\nМастер:"
        
        # Truncate context if it gets too long
        if len(prompt) > 2000:
            prompt = "..." + prompt[-2000:]

        try:
            # Generate
            response = self.generator(
                prompt, 
                max_new_tokens=150, 
                num_return_sequences=1,
                temperature=0.8,
                top_k=50,
                top_p=0.95,
                repetition_penalty=1.2, # Fix repetition
                do_sample=True,
                pad_token_id=50256
            )
            
            full_text = response[0]['generated_text']
            # Extract just the new part
            new_content = full_text[len(prompt):].strip()
            
            # Clean up potential partial sentences or "Player:" hallucinations
            if "Player:" in new_content:
                new_content = new_content.split("Player:")[0].strip()
            
            return new_content
        except Exception as e:
            print(f"Error generating story: {e}")
            return "Something went wrong in the dungeon..."
