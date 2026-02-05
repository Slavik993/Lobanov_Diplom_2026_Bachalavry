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
        # Smart detection: If input is long (>50 chars), it's likely a story/narrative, not a student question.
        # In that case, we should NOT use the "Lecturer/Student" rigid structure which causes hallucinations.
        is_narrative = len(user_input) > 50 and user_input.count(' ') > 5
        
        if educational_mode and not is_narrative:
             # Strict Educational Mode (Topics, Questions)
             # Try to keep it strict
             prompt = f"{context}\nСтудент: {user_input}\nЛектор:"
        elif is_narrative:
             # Narrative Mode (Story/Comic) - Just continue the text or use a storyteller persona
             # We use a neutral prompt to let the model continue the story naturally
             prompt = f"{context}\nТекст: {user_input}\nПродолжение:"
        else:
             prompt = f"{context}\nИгрок: {user_input}\nМастер:"
        
        # Truncate context if it gets too long
        if len(prompt) > 2000:
            prompt = "..." + prompt[-2000:]
            
        # ... generation code ...

        try:
            # Generate
            response = self.generator(
                prompt,
                max_new_tokens=150, 
                num_return_sequences=1,
                temperature=0.8,
                top_k=50,
                top_p=0.95,
                repetition_penalty=1.2,
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

    def generate_visual_storyboard(self, topic, style, count=4):
        """
        Generates a sequence of visual descriptions for a storyboard.
        Returns a list of strings, one for each frame.
        """
        if not self.generator:
            return [f"Frame {i+1} of {topic}" for i in range(count)]

        # Prompt strategies for different styles
        if style == "Algorithm Flowchart":
            system_instruction = (
                f"Опиши {count} кадров анимации, объясняющей алгоритм '{topic}'. "
                "Каждый кадр должен показывать изменения данных. "
                "Формат: 'Кадр 1: [описание]'. Без лишних слов."
            )
        elif style == "Neural Network":
            system_instruction = (
                f"Опиши {count} этапов обучения нейросети по теме '{topic}'. "
                "Визуализируй поток данных. "
                "Формат: 'Кадр 1: [описание]'."
            )
        else:
            system_instruction = (
                f"Create a storyboard of {count} frames for '{topic}' in style '{style}'. "
                "Describe visual action in each frame. "
                "Format: 'Frame 1: [description]'."
            )

        prompt = f"{system_instruction}\n"
        
        try:
            response = self.generator(
                prompt,
                max_new_tokens=300,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=50256
            )
            
            full_text = response[0]['generated_text'][len(prompt):]
            
            # Parse frames
            frames = []
            current_frame = ""
            
            # Simple parsing logic assuming "Frame X:" or "Кадр X:" format
            lines = full_text.split('\n')
            for line in lines:
                if "1:" in line or "1 :" in line:
                    if current_frame: frames.append(current_frame.strip())
                    current_frame = line
                elif any(f"{i}:" in line for i in range(2, count+2)):
                     if current_frame: frames.append(current_frame.strip())
                     current_frame = line
                else:
                    current_frame += " " + line
            
            if current_frame:
                frames.append(current_frame.strip())
            
            # Fallback if parsing failed
            if len(frames) < count:
                print(f"Storyboard parsing failed or incomplete (got {len(frames)} frames). Using fallback.")
                # Fallback to generic sequential steps if LLM fails
                frames = [f"{topic}, step {i+1}, visual representation" for i in range(count)]
                
            return frames[:count]

        except Exception as e:
            print(f"Error generating storyboard: {e}")
            return [f"{topic}, scene {i+1}" for i in range(count)]
