import gradio as gr
from core.translator import Translator
from core.text_processing import TextProcessor
from core.generator import ImageGenerator
from core.storyteller import StoryTeller
from core.prompt_engineering import PromptEngineer
from core.session_manager import SessionManager
from utils.config import config
from utils.logger import app_logger
import os
import random
import uuid

# Инициализация модулей
translator = Translator()
text_processor = TextProcessor()
generator = ImageGenerator()
storyteller = StoryTeller(model_name="ai-forever/rugpt3small_based_on_gpt2", device="cpu") 
prompt_engineer = PromptEngineer()
session_manager = SessionManager(storage_path=config.get("paths.sessions_dir", "sessions"))

# Глобальное состояние
class SessionState:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.history = ""
        self.current_seed = -1
        self.char_desc = ""
        self.style = ""
        self.images = []

    def reset(self):
        self.session_id = str(uuid.uuid4())
        self.history = ""
        self.current_seed = random.randint(0, 1000000)
        self.char_desc = ""
        self.style = ""
        self.images = []

session = SessionState()

def generate_sequence(base_prompt_ru, character, style, count=3):
    """Generates a sequence of related images."""
    images = []
    
    # Base extraction
    visual_text = text_processor.extract_visual_part(base_prompt_ru)
    
    # Variations for sequence
    # For a simple CPU approach, we can just use the same prompt or slightly vary random seed 
    # OR vary the prompt slightly (e.g. "establishing shot", "action", "close up")
    
    variations = ["cinematic shot", "action shot, dynamic", "close up, detailed expression"]
    
    for i in range(count):
        variation = variations[i % len(variations)]
        
        complex_prompt = prompt_engineer.build_prompt(
            base_description=f"{visual_text}, {variation}", 
            style_name="Cinematic", 
            character_desc=character,
            add_random_camera=False
        )
        
        en_prompt = translator.translate(complex_prompt)
        app_logger.info(f"Generating frame {i+1}: {en_prompt}")
        
        # Use same seed for consistency or slight variation?
        # Standard consistency: Same Seed.
        img = generator.generate(en_prompt, seed=session.current_seed)
        images.append(img)
        
    return images

def start_story(character_input, style_input):
    """Initializes the story session."""
    session.reset()
    session.char_desc = character_input
    session.style = style_input
    
    app_logger.info(f"Starting new session: {session.session_id}")
    app_logger.info(f"Character: {character_input}, Style: {style_input}")
    
    # Generate intro
    intro_prompt = f"История начинается. Главный герой: {character_input}. Жанр: {style_input}. Начало:"
    intro_text = storyteller.generate_response("Вступление:", intro_prompt)
    session.history = f"Система: История о {character_input}.\nМастер: {intro_text}"
    
    # Generate Sequence
    imgs = generate_sequence(intro_text, character_input, style_input)
    session.images.extend(imgs)
    
    # Save session
    session_manager.save_session(
        session.session_id, 
        session.history, 
        session.char_desc, 
        session.style, 
        session.current_seed
    )
    
    # Return format: List of [User, Bot] dicts
    return [
        {"role": "assistant", "content": intro_text}
    ], imgs

def chat_turn(user_message, chat_history):
    """Handles a single turn of the chat."""
    if not user_message:
        return chat_history, None

    app_logger.info(f"User message: {user_message}")

    # Update history
    session.history += f"\nИгрок: {user_message}"
    
    # Generate Text Response
    response_text = storyteller.generate_response(session.history, user_message)
    session.history += f"\nМастер: {response_text}"
    
    # Generate Sequence
    imgs = generate_sequence(response_text, session.char_desc, session.style)
    session.images.extend(imgs)
    
    # Update chat history
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": response_text})
    
    # Save session
    session_manager.save_session(
        session.session_id, 
        session.history, 
        session.char_desc, 
        session.style, 
        session.current_seed
    )
    
    return chat_history, imgs

with gr.Blocks(title=config.get("app_name", "StoryForge Lite"), theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ⚔️ StoryForge Lite: Нелинейные Приключения")
    
    with gr.Row():
        with gr.Column(scale=1):
            # Setup Column
            char_input = gr.Textbox(label="Ваш Герой", placeholder="Рыцарь в сияющих доспехах")
            style_input = gr.Textbox(label="Стиль Мира", value="Dark Fantasy, Detailed, Cinematic")
            start_btn = gr.Button("Начать Приключение", variant="primary")
            
            # Current Scene Gallery
            scene_gallery = gr.Gallery(label="Текущая Сцена (Последовательность)", columns=[1], rows=[3], object_fit="contain", height="auto")
            
        with gr.Column(scale=2):
            # Chat Interface
            chatbot = gr.Chatbot(label="История", height=600)
            msg_input = gr.Textbox(label="Ваши Действия", placeholder="Что вы хотите сделать?")
            send_btn = gr.Button("Отправить")

    # Events
    # Events
    start_btn.click(
        fn=start_story,
        inputs=[char_input, style_input],
        outputs=[chatbot, scene_gallery]
    )
    
    send_btn.click(
        fn=chat_turn,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, scene_gallery]
    )
    msg_input.submit(
        fn=chat_turn,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, scene_gallery]
    )

if __name__ == "__main__":
    demo.launch()
