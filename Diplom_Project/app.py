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
generator = ImageGenerator(low_memory_mode=True)  # Enable low memory mode for 8GB RAM
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
        self.educational_mode = False

    def reset(self):
        self.session_id = str(uuid.uuid4())
        self.history = ""
        self.current_seed = random.randint(0, 1000000) if not self.educational_mode else self.current_seed
        self.char_desc = ""
        self.style = ""
        self.images = []

session = SessionState()

def generate_sequence(base_prompt_ru, character, style, count=3, educational_mode=False):
    """Generates a sequence of related images."""
    images = []
    
    # Base extraction
    visual_text = text_processor.extract_visual_part(base_prompt_ru)
    is_split_narrative = False
    context_anchor = ""
    
    # Check if this is a long user story/plot (Comic Mode)
    if len(base_prompt_ru) > 50 and base_prompt_ru.count(' ') > 5:
        app_logger.info(f"Detected long story input. Splitting into scenes...")
        variations = text_processor.split_story_into_scenes(base_prompt_ru, num_scenes=count)
        is_split_narrative = True
        # Extract the first sentence as the "Context Anchor" (Subject + Setting)
        # This ensures Frame 2 ("He lights a torch") knows who "He" is (from Frame 1 "Knight enters castle")
        context_anchor = base_prompt_ru.split('.')[0].strip()
        if len(context_anchor) > 100:
            context_anchor = context_anchor[:100] # Truncate if first sentence is huge
    
    # IT-specific variations based on style and content
    elif educational_mode:
        app_logger.info(f"Generating storyboard for: {character} using style {style}")
        variations = storyteller.generate_visual_storyboard(character, style, count)
        if not variations or len(variations) < count:
             variations = ["informational diagram", "detailed schematic", "process flow", "summary result"]
    elif style == "Algorithm Flowchart":
        variations = [
            "flowchart diagram with start/stop ovals",
            "pseudocode structure",
            "trace table",
            "call stack hierarchy"
        ]
    else:
        variations = ["cinematic shot", "action shot, dynamic", "close up"]
    
    for i in range(count):
        variation = variations[i % len(variations)]
        
        # Prompt Logic:
        if is_split_narrative:
            # We combine the Context Anchor (Who/Where) with the specific Action (Variation)
            # Example: "Knight enters dark castle" (Context) + "He lights a torch" (Action)
            description_input = variation
            char_context = context_anchor
        else:
            description_input = f"{visual_text}, {variation}"
            char_context = character

        complex_prompt, negative_prompt = prompt_engineer.build_prompt(
            base_description=description_input, 
            style_name=style, 
            character_desc=char_context,
            add_random_camera=False,
            educational_mode=educational_mode
        )
        
        en_prompt = translator.translate(complex_prompt)
        # Ensure 'high quality' is strictly enforced
        if "high quality" not in en_prompt.lower():
            en_prompt += ", high quality, 8k, masterpiece"
            
        en_negative_prompt = translator.translate(negative_prompt) if negative_prompt else ""
        app_logger.info(f"Generating frame {i+1}: {en_prompt}")
        if en_negative_prompt:
            app_logger.info(f"Negative prompt: {en_negative_prompt}")
        
        # Seed Logic:
        # For Narratives/Comics, use the SAME seed for all frames to keep character/style consistent.
        # For Topics, vary the seed to show different details/layouts.
        if is_split_narrative:
             scene_seed = session.current_seed # Constant seed
        else:
             scene_seed = session.current_seed + i if session.current_seed != -1 else None

        img = generator.generate(en_prompt, negative_prompt=en_negative_prompt, seed=scene_seed, educational_mode=educational_mode)
        images.append(img)
        
    return images

def start_story(character_input, style_input, educational_mode, scene_count):
    """Initializes the story session."""
    session.reset()
    session.char_desc = character_input
    session.style = style_input
    session.educational_mode = educational_mode
    
    app_logger.info(f"Starting new session: {session.session_id}")
    app_logger.info(f"Character: {character_input}, Style: {style_input}, Educational: {educational_mode}, Scenes: {scene_count}")
    
    # Smart Detection: Is this a Story or a Topic?
    is_narrative = len(character_input) > 50 and character_input.count(' ') > 5
    
    if is_narrative:
        # Narrative Mode: Visualize the user's text directly!
        intro_text = character_input
        session.history = f"Система: Визуализация сюжета.\nСюжет: {character_input}"
        # We don't ask the LLM to generate text, we just say "Here is your visualization"
        chat_output = "Генерирую визуальный ряд по вашему сюжету..."
        
        # Determine strict mode for prompt engineering based on style
        # If Comic Book, we want to enforce it even if Educational is checked
        if style_input == "Comic Book":
             # We might want to pass educational_mode=False to generate_sequence to avoid "simple background" logic
             # But let's handle that in PromptEngineer mostly.
             pass
    else:
        # Topic Mode: Generate educational intro
        if educational_mode:
            intro_prompt = f"Тема занятия: {character_input}. Стиль изложения: {style_input}. Введение:"
            intro_text = storyteller.generate_response("Лекция началась.", intro_prompt, educational_mode=True)
            session.history = f"Система: Занятие на тему '{character_input}'.\nЛектор: {intro_text}"
        else:
            intro_prompt = f"История начинается. Главный герой: {character_input}. Жанр: {style_input}. Начало:"
            intro_text = storyteller.generate_response("Вступление:", intro_prompt, educational_mode=False)
            session.history = f"Система: История о {character_input}.\nМастер: {intro_text}"
        chat_output = intro_text
    
    # Generate Sequence
    # IMPORTANT: If narrative, intro_text IS the narrative. If topic, intro_text IS the generated lecture.
    imgs = generate_sequence(intro_text, character_input, style_input, count=scene_count, educational_mode=educational_mode)
    session.images.extend(imgs)
    
    # Save session
    session_manager.save_session(
        session.session_id, 
        session.history, 
        session.char_desc, 
        session.style, 
        session.current_seed,
        session.educational_mode,
        images=session.images
    )
    
    # Return format: List of [User, Bot] dicts
    chat_history = [
        {"role": "assistant", "content": chat_output}
    ]
    
    # Save session with chat history
    session_manager.save_session(
        session.session_id, 
        session.history, 
        session.char_desc, 
        session.style, 
        session.current_seed,
        session.educational_mode,
        images=session.images,
        chat_history=chat_history
    )
    
    return chat_history, imgs

def chat_turn(user_message, chat_history):
    """Handles a single turn of the chat."""
    if not user_message:
        return chat_history, None

    app_logger.info(f"User message: {user_message}")

    # Update history
    if session.educational_mode:
        session.history += f"\nСтудент: {user_message}"
    else:
        session.history += f"\nИгрок: {user_message}"
    
    # Generate Text Response
    response_text = storyteller.generate_response(session.history, user_message, educational_mode=session.educational_mode)
    
    if session.educational_mode:
        session.history += f"\nЛектор: {response_text}"
    else:
        session.history += f"\nМастер: {response_text}"
    
    # Generate Sequence
    imgs = generate_sequence(response_text, session.char_desc, session.style, educational_mode=session.educational_mode)
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
        session.current_seed,
        session.educational_mode,
        images=session.images,
        chat_history=chat_history or [] # Pass the structured chat history
    )
    
    return chat_history, imgs

def import_session_handler(file_obj):
    """Handles session import from a JSON file."""
    if file_obj is None:
        return None, [], "Файл не выбран"
    
    try:
        data = session_manager.import_session_file(file_obj.name)
        if not data:
            return None, [], "Не удалось загрузить файл сессии"
            
        # Restore session state
        session.session_id = data.get("session_id", str(uuid.uuid4()))
        session.history = data.get("history", "")
        session.char_desc = data.get("character", "")
        session.style = data.get("style", "")
        session.current_seed = data.get("seed", -1)
        session.educational_mode = data.get("educational_mode", False)
        
        # Restore chat history (list of dicts)
        restored_chat = data.get("chat_history", [])
        
        # If no structured chat history exists (old save), try to rebuild from string history (basic fallback)
        if not restored_chat and session.history:
             # Basic reconstruction if needed, or just leave empty to avoid errors
             restored_chat = [{"role": "assistant", "content": "История восстановлена из старого формата (текст): " + session.history[:100] + "..."}]
        
        # Restore images (paths might be relative or need checking)
        saved_images = data.get("saved_images", [])
        session.images = [] # We can't easily load PIL images from paths without reopening them
        
        # Try to reload images for the gallery
        gallery_images = []
        for img_path in saved_images:
            if os.path.exists(img_path):
                 gallery_images.append(img_path)
            else:
                 # Try relative to the json file if absolute fail
                 base_dir = os.path.dirname(file_obj.name)
                 rel_path = os.path.join(base_dir, os.path.basename(img_path))
                 if os.path.exists(rel_path):
                     gallery_images.append(rel_path)

        app_logger.info(f"Session imported: {session.session_id}")
        return restored_chat, gallery_images, f"Сессия загружена: {session.char_desc}"

    except Exception as e:
        app_logger.error(f"Import error: {e}")
        return [], [], f"Ошибка импорта: {e}"

with gr.Blocks(title="Neuro Tale: Генератор образовательных визуалов", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎓 Neuro Tale: Генератор визуалов для IT-образования")
    gr.Markdown("**Специализированная система для создания учебно-методических материалов по:**")
    gr.Markdown("- Алгоритмизации и программированию")
    gr.Markdown("- Интеллектуальному анализу данных") 
    gr.Markdown("- Машинному обучению и ИИ")
    gr.Markdown("- Реляционным базам данных")
    gr.Markdown("- Веб-разработке")
    gr.Markdown("- Разработке интерфейсов")
    
    with gr.Row():
        with gr.Column(scale=1):
            # Setup Column
            char_input = gr.Textbox(
                label="Тема / Концепция / Сюжет", 
                placeholder="Например: 'Рыцарь входит в замок...'"
            )
            style_input = gr.Dropdown(
                label="Стиль визуализации", 
                choices=prompt_engineer.get_available_styles(), 
                value="Educational",
                info="Выберите подходящий стиль"
            )
            educational_checkbox = gr.Checkbox(
                label="Учебно-методический режим", 
                value=True,
                info="Оставьте включенным для генерации диаграмм и схем. Для комиксов можно отключить, но система сама поймет сюжет."
            )
            scene_count_slider = gr.Slider(label="Количество сцен", minimum=1, maximum=5, value=3, step=1)
            low_memory_checkbox = gr.Checkbox(label="Режим 8GB RAM (низкое качество)", value=False)
            
            start_btn = gr.Button("🚀 Создать последовательность", variant="primary")
            
            # Import Section
            gr.Markdown("---")
            import_file = gr.File(label="Загрузить сессию (.json)", file_types=[".json"])
            import_status = gr.Textbox(label="Статус импорта", interactive=False)
            
            # Current Scene Gallery
            scene_gallery = gr.Gallery(
                label="Сгенерированная последовательность", 
                columns=[1], 
                rows=[3], 
                object_fit="contain", 
                height="auto"
            )
            
        with gr.Column(scale=2):
            # Chat Interface
            chatbot = gr.Chatbot(label="История / Сценарий", height=600)
            msg_input = gr.Textbox(
                label="Дополнительные инструкции / Продолжение сюжета", 
                placeholder="Например: 'Далее он поднимает меч...'"
            )
            send_btn = gr.Button("Дополнить последовательность")

    # Events
    # Events
    start_btn.click(
        fn=start_story,
        inputs=[char_input, style_input, educational_checkbox, scene_count_slider],
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
    
    import_file.change(
        fn=import_session_handler,
        inputs=[import_file],
        outputs=[chatbot, scene_gallery, import_status]
    )

if __name__ == "__main__":
    demo.launch(share=True)
