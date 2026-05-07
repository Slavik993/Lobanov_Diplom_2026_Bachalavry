"""
Интеллектуальная система генерации последовательности изображений по текстовому сюжету
Улучшенная версия с CPU/GPU поддержкой и современным интерфейсом

Автор: Шебанов Вячеслав (улучшения на основе Rotation_T2I_to_T2V)
"""

import torch
import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import sys
import json
import hashlib
import warnings
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import random

warnings.filterwarnings('ignore')

# ==================== КОНФИГУРАЦИЯ ====================

class Config:
    """Конфигурация приложения"""
    APP_NAME = "StoryForge AI"
    VERSION = "2.0.0"
    
    # Пути
    OUTPUT_DIR = Path("outputs")
    SESSIONS_DIR = Path("sessions")
    CACHE_DIR = Path("cache")
    
    # Модели
    DEFAULT_MODEL = "runwayml/stable-diffusion-v1-5"
    FALLBACK_MODEL = "CompVis/stable-diffusion-v1-4"
    
    # Генерация
    DEFAULT_STEPS = 20
    DEFAULT_HEIGHT = 384
    DEFAULT_WIDTH = 384
    CPU_STEPS = 15  # Меньше шагов для CPU
    CPU_SIZE = 256  # Меньший размер для CPU
    
    # Стили
    STYLES = {
        "Cinematic": "cinematic lighting, movie scene, film grain, dramatic lighting",
        "Anime": "anime style, manga illustration, studio ghibli, vibrant colors",
        "Photorealistic": "photorealistic, 8k uhd, professional photography, sharp focus",
        "Digital Art": "digital art, concept art, trending on artstation, highly detailed",
        "Oil Painting": "oil painting, classical art, canvas texture, masterpiece",
        "Cyberpunk": "cyberpunk, neon lights, futuristic, sci-fi, dystopian",
        "Fantasy": "fantasy art, magical atmosphere, ethereal, mystical lighting",
        "Watercolor": "watercolor painting, soft colors, artistic, flowing paint"
    }

# Создаем директории
for dir_path in [Config.OUTPUT_DIR, Config.SESSIONS_DIR, Config.CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ==================== УТИЛИТЫ ====================

def get_device_info() -> Tuple[str, str, bool]:
    """Получает информацию об устройстве"""
    if torch.cuda.is_available():
        device = "cuda"
        device_name = torch.cuda.get_device_name(0)
        is_gpu = True
    else:
        device = "cpu"
        device_name = "CPU (Intel/AMD)"
        is_gpu = False
    return device, device_name, is_gpu

def flush_memory():
    """Очистка памяти"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    import gc
    gc.collect()

def create_placeholder_image(text: str, size: Tuple[int, int] = (384, 384)) -> Image.Image:
    """Создает placeholder изображение с текстом"""
    # Генерируем цвет на основе текста
    hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
    r = (hash_val % 200) + 55
    g = ((hash_val // 256) % 200) + 55
    b = ((hash_val // 65536) % 200) + 55
    
    img = Image.new('RGB', size, color=(20, 20, 30))
    draw = ImageDraw.Draw(img)
    
    # Градиент фона
    for i in range(size[1]):
        alpha = i / size[1]
        color = (
            int(20 + (r - 20) * alpha * 0.3),
            int(20 + (g - 20) * alpha * 0.3),
            int(30 + (b - 30) * alpha * 0.3)
        )
        draw.line([(0, i), (size[0], i)], fill=color)
    
    # Добавляем текст
    words = text.split()[:6]
    display_text = ' '.join(words) if words else text[:30]
    
    # Рамка
    margin = 20
    draw.rectangle(
        [margin, size[1]//2 - 40, size[0] - margin, size[1]//2 + 40],
        outline=(255, 255, 255, 128),
        width=2
    )
    
    return img

# ==================== ОБРАБОТКА ТЕКСТА ====================

class TextProcessor:
    """Обработка текстовых сюжетов"""
    
    def __init__(self):
        self.scene_indicators = [
            "внезапно", "потом", "затем", "вдруг", "в это время",
            "через некоторое время", "спустя", "вскоре", "наконец",
            "после", "когда", "тем временем", "в то время как"
        ]
        
        self.enhancements = [
            "high quality, detailed, professional",
            "beautiful composition, artistic, masterpiece",
            "sharp focus, well lit, clear details",
            "stunning visuals, impressive, captivating"
        ]
    
    def split_story(self, text: str, num_scenes: int = 4) -> List[str]:
        """Разбивает сюжет на сцены"""
        text = ' '.join(text.strip().split())
        
        # Разбиваем по предложениям
        sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
        
        if not sentences:
            return ["Empty scene"] * num_scenes
        
        # Если предложений меньше чем сцен - дублируем
        while len(sentences) < num_scenes:
            sentences.append(sentences[-1])
        
        # Распределяем по сценам
        scenes = []
        chunk_size = len(sentences) / num_scenes
        
        for i in range(num_scenes):
            start = int(i * chunk_size)
            end = int((i + 1) * chunk_size) if i < num_scenes - 1 else len(sentences)
            scene_text = " ".join(sentences[start:end])
            scenes.append(scene_text if scene_text else sentences[min(start, len(sentences)-1)])
        
        return scenes
    
    def enhance_prompt(self, scene_text: str, style: str = "", add_quality: bool = True) -> str:
        """Улучшает промпт для генерации"""
        style_prompt = Config.STYLES.get(style, "")
        
        if add_quality and not any(x in scene_text.lower() for x in ["quality", "detailed", "masterpiece"]):
            enhancement = random.choice(self.enhancements)
            return f"{style_prompt} {scene_text}, {enhancement}".strip()
        
        return f"{style_prompt} {scene_text}".strip()
    
    def analyze_story(self, text: str) -> Dict:
        """Анализирует сюжет"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        words = text.split()
        
        # Определяем настроение
        positive_words = ['счастливый', 'радостный', 'красивый', 'светлый', 'добрый', 'любовь', 'победа']
        negative_words = ['страшный', 'темный', 'злой', 'грустный', 'страх', 'опасность', 'война']
        
        pos_count = sum(1 for w in words if any(pw in w.lower() for pw in positive_words))
        neg_count = sum(1 for w in words if any(nw in w.lower() for nw in negative_words))
        
        mood = "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "neutral"
        
        return {
            "sentence_count": len(sentences),
            "word_count": len(words),
            "estimated_scenes": min(max(len(sentences) // 2, 2), 6),
            "mood": mood,
            "has_dialogue": '"' in text or '"' in text
        }

# ==================== ГЕНЕРАТОР ИЗОБРАЖЕНИЙ ====================

class StoryImageGenerator:
    """Генератор изображений из сюжета"""
    
    def __init__(self, device: str = None, use_cpu_optimization: bool = False):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_cpu_optimization = use_cpu_optimization or (self.device == "cpu")
        self.pipeline = None
        self.is_loaded = False
        self.current_model = None
        
        self.text_processor = TextProcessor()
        
    def load_model(self, model_id: str = None, progress_callback=None):
        """Загружает модель Stable Diffusion"""
        if self.is_loaded and self.current_model == model_id:
            return True
        
        try:
            from diffusers import StableDiffusionPipeline
            
            model_id = model_id or Config.DEFAULT_MODEL
            
            if progress_callback:
                progress_callback(0.1, "Загрузка модели...")
            
            dtype = torch.float16 if self.device == "cuda" else torch.float32
            
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=dtype,
                safety_checker=None,
                requires_safety_checker=False,
                cache_dir=Config.CACHE_DIR
            )
            
            if progress_callback:
                progress_callback(0.5, "Оптимизация модели...")
            
            # Оптимизации
            if self.use_cpu_optimization:
                self.pipeline = self.pipeline.to("cpu")
                # CPU-оптимизации
                try:
                    self.pipeline.enable_sequential_cpu_offload()
                except:
                    pass
            else:
                self.pipeline = self.pipeline.to(self.device)
                # GPU-оптимизации
                try:
                    self.pipeline.enable_attention_slicing()
                    self.pipeline.enable_vae_slicing()
                except:
                    pass
            
            self.is_loaded = True
            self.current_model = model_id
            
            if progress_callback:
                progress_callback(1.0, "Модель готова!")
            
            return True
            
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            return False
    
    def generate_image(
        self, 
        prompt: str, 
        negative_prompt: str = "",
        seed: int = None,
        num_inference_steps: int = None,
        height: int = None,
        width: int = None,
        progress_callback=None
    ) -> Image.Image:
        """Генерирует одно изображение"""
        
        if not self.is_loaded:
            if not self.load_model(progress_callback=progress_callback):
                return create_placeholder_image(prompt)
        
        # Настройки в зависимости от устройства
        if self.use_cpu_optimization:
            steps = num_inference_steps or Config.CPU_STEPS
            h = height or Config.CPU_SIZE
            w = width or Config.CPU_SIZE
        else:
            steps = num_inference_steps or Config.DEFAULT_STEPS
            h = height or Config.DEFAULT_HEIGHT
            w = width or Config.DEFAULT_WIDTH
        
        seed = seed or random.randint(0, 1000000)
        generator = torch.Generator(device=self.device if not self.use_cpu_optimization else "cpu")
        generator.manual_seed(seed)
        
        negative = negative_prompt or "blurry, low quality, distorted, ugly, bad anatomy, watermark, signature"
        
        try:
            if progress_callback:
                progress_callback(0.3, "Генерация...")
            
            with torch.no_grad():
                result = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative,
                    num_inference_steps=steps,
                    guidance_scale=7.5,
                    generator=generator,
                    height=h,
                    width=w
                ).images[0]
            
            if progress_callback:
                progress_callback(1.0, "Готово!")
            
            flush_memory()
            return result
            
        except Exception as e:
            print(f"Ошибка генерации: {e}")
            return create_placeholder_image(prompt, (w, h))
    
    def generate_sequence(
        self,
        story_text: str,
        num_scenes: int = 4,
        style: str = "",
        seed_start: int = 42,
        progress_callback=None
    ) -> Tuple[List[Image.Image], List[str], List[str]]:
        """Генерирует последовательность изображений"""
        
        # Анализ и разбиение
        scenes = self.text_processor.split_story(story_text, num_scenes)
        analysis = self.text_processor.analyze_story(story_text)
        
        images = []
        prompts = []
        
        for i, scene in enumerate(scenes):
            if progress_callback:
                progress_callback(i / num_scenes, f"Генерация сцены {i+1}/{num_scenes}...")
            
            # Улучшаем промпт
            enhanced = self.text_processor.enhance_prompt(scene, style)
            prompts.append(enhanced)
            
            # Генерируем с уникальным seed
            seed = seed_start + i * 100
            img = self.generate_image(
                enhanced, 
                seed=seed,
                progress_callback=lambda p, t: progress_callback(
                    (i + p) / num_scenes, 
                    f"Сцена {i+1}: {t}"
                ) if progress_callback else None
            )
            images.append(img)
        
        return images, prompts, scenes

# ==================== ИНТЕРФЕЙС ====================

def create_interface():
    """Создает Gradio интерфейс"""
    
    # Информация о системе
    device, device_name, is_gpu = get_device_info()
    
    # CSS для стилизации
    css = """
    .main-container {
        max-width: 1200px !important;
        margin: 0 auto;
    }
    .header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    .scene-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px;
        background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .scene-number {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }
    .progress-bar {
        height: 8px;
        background: #e0e0e0;
        border-radius: 4px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        transition: width 0.3s ease;
    }
    .info-box {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }
    .image-gallery {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
    }
    """
    
    # Инициализация генератора
    generator = StoryImageGenerator()
    
    with gr.Blocks(title=f"{Config.APP_NAME} v{Config.VERSION}", css=css) as demo:
        
        # Header
        gr.HTML(f"""
        <div class="header">
            <h1>🎬 {Config.APP_NAME}</h1>
            <p>Генерация последовательности изображений по текстовому сюжету</p>
            <p style="font-size: 0.9em; opacity: 0.9;">
                Устройство: {device_name} {'✓ GPU' if is_gpu else '⚡ CPU'}
            </p>
        </div>
        """)
        
        with gr.Row():
            # Левая колонка - ввод
            with gr.Column(scale=1):
                
                gr.Markdown("### 📝 Введите ваш сюжет")
                
                story_input = gr.Textbox(
                    label="Текст истории",
                    placeholder="Например: Маленький мальчик шел через лес. Вдруг он увидел старый замок...",
                    lines=6,
                    max_lines=10
                )
                
                # Примеры
                gr.Markdown("**Быстрые примеры:**")
                examples = gr.Examples(
                    examples=[
                        ["Космонавт летит на велосипеде по поверхности Марса. Вдали виднеются две луны. Он находит странный светящийся артефакт.", 4, "Sci-Fi"],
                        ["Кот в костюме супергероя спасает птичку с дерева. Горожане аплодируют. Солнце садится за горизонт.", 3, "Anime"],
                        ["Волшебник читает древнюю книгу в библиотеке. Книга начинает светиться. Из нее появляется маленький дракон.", 4, "Fantasy"],
                        ["Робот-шеф готовит пиццу на космической станции. Ингредиенты плавают в невесомости. Астронавты наблюдают.", 3, "Cinematic"],
                    ],
                    inputs=[story_input],
                    label=""
                )
                
                # Настройки
                with gr.Accordion("⚙️ Настройки генерации", open=False):
                    
                    num_scenes = gr.Slider(
                        minimum=1,
                        maximum=8,
                        value=4,
                        step=1,
                        label="Количество сцен"
                    )
                    
                    style_dropdown = gr.Dropdown(
                        choices=list(Config.STYLES.keys()),
                        value="Cinematic",
                        label="Стиль изображений"
                    )
                    
                    seed_input = gr.Number(
                        value=42,
                        label="Seed (для воспроизводимости)",
                        precision=0
                    )
                    
                    with gr.Row():
                        height_dropdown = gr.Dropdown(
                            choices=[256, 384, 512],
                            value=384 if is_gpu else 256,
                            label="Высота"
                        )
                        width_dropdown = gr.Dropdown(
                            choices=[256, 384, 512],
                            value=384 if is_gpu else 256,
                            label="Ширина"
                        )
                    
                    if not is_gpu:
                        cpu_opt = gr.Checkbox(
                            value=True,
                            label="CPU оптимизация (рекомендуется)",
                            info="Уменьшает качество, но ускоряет генерацию"
                        )
                    else:
                        cpu_opt = gr.Checkbox(
                            value=False,
                            visible=False
                        )
                
                # Кнопки
                with gr.Row():
                    generate_btn = gr.Button(
                        "✨ Сгенерировать историю",
                        variant="primary",
                        size="lg"
                    )
                    clear_btn = gr.Button("🗑️ Очистить", size="lg")
                
                # Статус
                status_text = gr.Textbox(
                    label="Статус",
                    value="Готов к работе",
                    interactive=False
                )
                
                progress_bar = gr.Slider(
                    minimum=0,
                    maximum=1,
                    value=0,
                    label="Прогресс",
                    interactive=False
                )
            
            # Правая колонка - вывод
            with gr.Column(scale=2):
                
                # Анализ сюжета
                analysis_box = gr.HTML(
                    label="Анализ сюжета",
                    value="<div class='info-box'>Введите сюжет для анализа</div>"
                )
                
                # Галерея изображений
                gr.Markdown("### 🖼️ Сгенерированные сцены")
                
                # Динамическое количество выходов
                gallery_outputs = []
                with gr.Row():
                    for i in range(8):
                        with gr.Column(visible=(i < 4), scale=1) as col:
                            img = gr.Image(
                                label=f"Сцена {i+1}",
                                type="pil",
                                interactive=False,
                                height=300
                            )
                            gallery_outputs.append((col, img))
                
                # Промпты
                with gr.Accordion("📋 Показать использованные промпты", open=False):
                    prompts_output = gr.JSON(label="Промпты")
                
                # Скачивание
                with gr.Row(visible=False) as download_row:
                    download_btn = gr.Button("💾 Скачать все изображения", variant="secondary")
                    zip_output = gr.File(label="Архив")
        
        # Функции обработки
        
        def update_visibility(num_scenes):
            """Обновляет видимость сцен"""
            updates = []
            for i in range(8):
                updates.append(gr.update(visible=(i < num_scenes)))  # Column
                updates.append(gr.update(visible=(i < num_scenes)))  # Image
            return updates
        
        def analyze_story_text(text):
            """Анализирует текст сюжета"""
            if not text or len(text) < 10:
                return "<div class='info-box'>Введите сюжет для анализа</div>"
            
            processor = TextProcessor()
            analysis = processor.analyze_story(text)
            
            html = f"""
            <div class='info-box'>
                <h4>📊 Анализ сюжета</h4>
                <p><strong>Предложений:</strong> {analysis['sentence_count']} | 
                   <strong>Слов:</strong> {analysis['word_count']} | 
                   <strong>Рекомендуется сцен:</strong> {analysis['estimated_scenes']}</p>
                <p><strong>Настроение:</strong> {analysis['mood']} | 
                   <strong>Диалоги:</strong> {'Да' if analysis['has_dialogue'] else 'Нет'}</p>
            </div>
            """
            return html
        
        def generate_story(story, num_scenes_val, style, seed, height, width, cpu_optimization):
            """Генерация истории"""
            if not story or len(story) < 10:
                return [gr.update()] * 16 + ["Введите сюжет (минимум 10 символов)"]
            
            # Обновляем настройки генератора
            generator.use_cpu_optimization = cpu_optimization
            
            images = []
            status_messages = []
            
            def progress_callback(progress, message):
                status_messages.append((progress, message))
            
            try:
                # Генерация
                result_images, prompts, scenes = generator.generate_sequence(
                    story,
                    num_scenes=num_scenes_val,
                    style=style,
                    seed_start=int(seed),
                    progress_callback=progress_callback
                )
                
                # Формируем выход
                outputs = []
                for i in range(8):
                    if i < len(result_images):
                        outputs.append(gr.update(visible=True))  # Column
                        outputs.append(result_images[i])  # Image
                    else:
                        outputs.append(gr.update(visible=False))  # Column
                        outputs.append(None)  # Image
                
                # Промпты
                prompts_dict = {f"Сцена {i+1}": p for i, p in enumerate(prompts)}
                outputs.append(prompts_dict)
                outputs.append(gr.update(visible=True))  # download_row
                outputs.append("✅ Генерация завершена!")
                outputs.append(1.0)  # progress
                
                return outputs
                
            except Exception as e:
                return [gr.update()] * 16 + [f"❌ Ошибка: {str(e)}"]
        
        def clear_all():
            """Очистка всех полей"""
            updates = ["", 4, "Cinematic", 42, 384, 384, True]  # Inputs
            updates += [gr.update(visible=(i < 4)) for i in range(8)]  # Columns
            updates += [None] * 8  # Images
            updates += [{}]  # Prompts
            updates += [gr.update(visible=False)]  # Download row
            updates += ["Готов к работе"]  # Status
            updates += [0]  # Progress
            return updates
        
        # Обработчики событий
        num_scenes.change(
            fn=update_visibility,
            inputs=[num_scenes],
            outputs=[item for pair in gallery_outputs for item in [pair[0], pair[1]]]
        )
        
        story_input.change(
            fn=analyze_story_text,
            inputs=[story_input],
            outputs=[analysis_box]
        )
        
        generate_btn.click(
            fn=generate_story,
            inputs=[story_input, num_scenes, style_dropdown, seed_input, 
                   height_dropdown, width_dropdown, cpu_opt],
            outputs=[item for pair in gallery_outputs for item in [pair[0], pair[1]]] + 
                   [prompts_output, download_row, status_text, progress_bar]
        )
        
        clear_btn.click(
            fn=clear_all,
            inputs=[],
            outputs=[story_input, num_scenes, style_dropdown, seed_input,
                    height_dropdown, width_dropdown, cpu_opt] +
                   [item for pair in gallery_outputs for item in [pair[0], pair[1]]] +
                   [prompts_output, download_row, status_text, progress_bar]
        )
        
        # Информация внизу
        gr.Markdown("""
        ---
        ### 💡 Советы по использованию:
        
        1. **Конкретность** - чем детальнее описание, тем лучше результат
        2. **Структура** - разделяйте сцены точками для лучшего распознавания
        3. **CPU vs GPU** - на CPU генерация занимает 2-3 минуты на изображение
        4. **Стили** - разные стили подходят для разных типов историй
        
        ### ⚠️ Требования:
        - **CPU**: 8GB RAM минимум, ~2-3 мин на изображение
        - **GPU**: NVIDIA с 4GB+ VRAM, ~10-20 сек на изображение
        
        **Версия:** {} | **Устройство:** {} | **Модель:** Stable Diffusion 1.5
        """.format(Config.VERSION, device_name))
    
    return demo

# ==================== ЗАПУСК ====================

def parse_args():
    """Парсинг аргументов командной строки"""
    import argparse
    parser = argparse.ArgumentParser(description=f'{Config.APP_NAME} v{Config.VERSION}')
    parser.add_argument('--cpu', action='store_true', help='Принудительный запуск в CPU-режиме')
    parser.add_argument('--port', type=int, default=7860, help='Порт для запуска (по умолчанию: 7860)')
    parser.add_argument('--share', action='store_true', help='Создать публичную ссылку Gradio')
    parser.add_argument('--no-optimization', action='store_true', help='Отключить CPU-оптимизации')
    parser.add_argument('--low-vram', action='store_true', help='Режим для видеокарт с малым объемом памяти')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    print("="*60)
    print(f"  {Config.APP_NAME} v{Config.VERSION}")
    print("="*60)
    
    device, device_name, is_gpu = get_device_info()
    
    # Принудительный CPU-режим
    if args.cpu:
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        device = 'cpu'
        is_gpu = False
        print("\n[⚡] Принудительный CPU-режим")
    
    print(f"\nУстройство: {device_name}")
    print(f"Режим: {'GPU' if is_gpu else 'CPU (оптимизировано)'}")
    
    if args.low_vram:
        print("[⚡] Режим низкой VRAM активирован")
    
    print(f"\nЗапуск интерфейса на порту {args.port}...")
    print(f"Откройте браузер по адресу: http://127.0.0.1:{args.port}")
    if args.share:
        print("Публичная ссылка будет создана")
    print("="*60)
    
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
        show_error=True,
        quiet=False,
        inbrowser=True
    )
