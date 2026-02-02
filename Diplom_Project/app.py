import gradio as gr
from core.translator import Translator
from core.text_processing import TextProcessor
from core.generator import ImageGenerator
from core.storyteller import StoryTeller
from core.prompt_engineering import PromptEngineer
from core.session_manager import SessionManager, SessionState
from utils.config import config
from utils.logger import app_logger
import os
import random
import uuid
import json
from datetime import datetime

# Инициализация модулей
translator = Translator()
text_processor = TextProcessor()
generator = ImageGenerator()
storyteller = StoryTeller(model_name="ai-forever/rugpt3small_based_on_gpt2", device="cpu") 
prompt_engineer = PromptEngineer()
session_manager = SessionManager(storage_path=config.get("paths.sessions_dir", "sessions"))

def generate_sequence(base_prompt_ru, character, style, seed, num_scenes, storyteller=None):
    """Generates a sequence of related images based on story progression."""
    images = []
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    story_dir = os.path.join(config.get("paths.output_dir", "outputs"), f"story_{timestamp}")
    os.makedirs(story_dir, exist_ok=True)
    
    scenes = []
    prompts = []
    story_context = f"История о {character}. Стиль: {style}. Начало: {base_prompt_ru}"
    
    for i in range(num_scenes):
        # Generate scene description using storyteller for coherence
        if storyteller and i > 0:
            scene_prompt = f"Опиши следующую сцену в истории: {story_context}. Сделай её логическим продолжением предыдущих событий."
            scene_description = storyteller.generate_response(story_context, scene_prompt, max_length=100)
            story_context += f"\nСцена {i+1}: {scene_description}"
        else:
            scene_description = base_prompt_ru
        
        # Extract visual part
        visual_text = text_processor.extract_visual_part(scene_description)
        
        # Build prompt with story context
        context = " ".join(scenes) if scenes else ""
        complex_prompt = prompt_engineer.build_prompt(
            base_description=f"{visual_text}, scene {i+1} of {num_scenes}, continuing the story", 
            style_name="Cinematic", 
            character_desc=character,
            add_random_camera=True,
            story_context=context
        )
        
        en_prompt = translator.translate(complex_prompt)
        app_logger.info(f"Generating frame {i+1}: {en_prompt}")
        
        # Use provided seed for consistency, but vary for each frame
        current_seed = seed + i * 1000 if seed != -1 else -1
        negative_prompt = "blurry, low quality, deformed, ugly, bad anatomy, watermark, text, signature"
        img = generator.generate(en_prompt, negative_prompt=negative_prompt, seed=current_seed, steps=50)
        images.append(img)
        
        # Save image
        img_path = os.path.join(story_dir, f"image_{i+1}.png")
        img.save(img_path)
        
        scenes.append(scene_description)
        prompts.append(en_prompt)
    
    # Save metadata
    metadata = {
        "original_story": base_prompt_ru,
        "scenes": scenes,
        "prompts": prompts,
        "timestamp": timestamp,
        "character": character,
        "style": style,
        "num_scenes": num_scenes
    }
    
    metadata_path = os.path.join(story_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
    
    return images, scenes

def start_story(character_input, style_input, num_scenes, state):
    """Initializes the story session."""
    if state is None:
        state = SessionState()
    
    state.reset()
    state.char_desc = character_input
    state.style = style_input
    state.num_scenes = num_scenes
    
    app_logger.info(f"Starting new session: {state.session_id}")
    app_logger.info(f"Character: {character_input}, Style: {style_input}, Num Scenes: {num_scenes}")
    
    # Generate intro
    intro_prompt = f"История начинается. Главный герой: {character_input}. Жанр: {style_input}. Начало:"
    intro_text = storyteller.generate_response("Вступление:", intro_prompt)
    state.history = f"Система: История о {character_input}.\nМастер: {intro_text}"
    
    # Generate Sequence
    imgs, scene_texts = generate_sequence(intro_text, character_input, style_input, state.current_seed, num_scenes, storyteller)
    state.images = imgs
    state.scene_texts = scene_texts
    
    # Save session
    session_manager.save_session(
        state.session_id, 
        state.history, 
        state.char_desc, 
        state.style, 
        state.current_seed,
        state.num_scenes
    )
    
    # Return format: List of [User, Bot] dicts, images with captions, updated state
    return [
        {"role": "assistant", "content": intro_text}
    ], [(img, text) for img, text in zip(imgs, scene_texts)], state

def chat_turn(user_message, chat_history, state):
    """Handles a single turn of the chat."""
    if not user_message:
        return chat_history, None, state
    
    if state is None:
        state = SessionState()
        state.reset()

    app_logger.info(f"User message: {user_message}")

    # Update history
    state.history += f"\nИгрок: {user_message}"
    
    # Generate Text Response
    response_text = storyteller.generate_response(state.history, user_message)
    state.history += f"\nМастер: {response_text}"
    
    # Generate Sequence
    imgs, scene_texts = generate_sequence(response_text, state.char_desc, state.style, state.current_seed, state.num_scenes, storyteller)
    state.images = imgs
    state.scene_texts = scene_texts
    
    # Update chat history
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": response_text})
    
    # Save session
    session_manager.save_session(
        state.session_id, 
        state.history, 
        state.char_desc, 
        state.style, 
        state.current_seed,
        state.num_scenes
    )
    
    return chat_history, [(img, text) for img, text in zip(imgs, scene_texts)], state

with gr.Blocks(title=config.get("app_name", "Neuro Tale"), theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ⚔️ Neuro Tale: Нелинейные Приключения")
    
    # State component for user session isolation
    session_state = gr.State()
    
    with gr.Row():
        with gr.Column(scale=1):
            # Setup Column
            char_input = gr.Textbox(label="Ваш Герой", placeholder="Рыцарь в сияющих доспехах")
            style_input = gr.Textbox(label="Стиль Мира", value="Dark Fantasy, Detailed, Cinematic")
            num_scenes_slider = gr.Slider(label="Количество сцен", minimum=1, maximum=10, value=3, step=1)
            start_btn = gr.Button("Начать Приключение", variant="primary")
            
            # Current Scene Gallery
            scene_gallery = gr.Gallery(label="Текущая Сцена (Последовательность)", columns=[1], rows=[3], object_fit="contain", height="auto")
            
        with gr.Column(scale=2):
            # Chat Interface
            # Chatbot receives list of dictionaries (messages format) implicitly supported by this version
            chatbot = gr.Chatbot(label="История", height=600)
            msg_input = gr.Textbox(label="Ваши Действия", placeholder="Что вы хотите сделать?")
            send_btn = gr.Button("Отправить")

    # Events
    start_btn.click(
        fn=start_story,
        inputs=[char_input, style_input, num_scenes_slider, session_state],
        outputs=[chatbot, scene_gallery, session_state]
    )
    
    send_btn.click(
        fn=chat_turn,
        inputs=[msg_input, chatbot, session_state],
        outputs=[chatbot, scene_gallery, session_state]
    )
    msg_input.submit(
        fn=chat_turn,
        inputs=[msg_input, chatbot, session_state],
        outputs=[chatbot, scene_gallery, session_state]
    )

if __name__ == "__main__":
    demo.launch(share=True)
