"""
Тестовый скрипт для проверки системы
"""

import sys
import os

def test_imports():
    """Тест импортов"""
    print("[1/5] Проверка библиотек...")
    try:
        import torch
        print(f"  ✓ PyTorch {torch.__version__}")
        print(f"    CUDA доступна: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"    Устройство: {torch.cuda.get_device_name(0)}")
    except ImportError:
        print("  ✗ PyTorch не установлен")
        return False
    
    try:
        import diffusers
        print(f"  ✓ Diffusers {diffusers.__version__}")
    except ImportError:
        print("  ✗ Diffusers не установлен")
        return False
    
    try:
        import transformers
        print(f"  ✓ Transformers {transformers.__version__}")
    except ImportError:
        print("  ✗ Transformers не установлен")
        return False
    
    try:
        import gradio
        print(f"  ✓ Gradio {gradio.__version__}")
    except ImportError:
        print("  ✗ Gradio не установлен")
        return False
    
    try:
        from PIL import Image
        print("  ✓ Pillow установлен")
    except ImportError:
        print("  ✗ Pillow не установлен")
        return False
    
    return True

def test_directories():
    """Тест директорий"""
    print("\n[2/5] Проверка директорий...")
    dirs = ['outputs', 'cache', 'sessions']
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"  ✓ Создана директория: {d}")
        else:
            print(f"  ✓ Директория существует: {d}")
    return True

def test_model_download():
    """Тест загрузки модели"""
    print("\n[3/5] Проверка модели...")
    try:
        from diffusers import StableDiffusionPipeline
        print("  ✓ Модель Stable Diffusion доступна")
        print("  ℹ Первый запуск загрузит ~5GB")
        return True
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        return False

def test_app():
    """Тест структуры приложения"""
    print("\n[4/5] Проверка структуры приложения...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'README.md',
        'QUICKSTART.md'
    ]
    
    for f in required_files:
        if os.path.exists(f):
            print(f"  ✓ {f}")
        else:
            print(f"  ✗ {f} не найден")
            return False
    
    return True

def test_generation():
    """Тест генерации"""
    print("\n[5/5] Тест генерации (placeholder)...")
    try:
        from app import create_placeholder_image, TextProcessor
        
        # Тест placeholder
        img = create_placeholder_image("Test scene")
        print(f"  ✓ Placeholder создан: {img.size}")
        
        # Тест текстового процессора
        processor = TextProcessor()
        scenes = processor.split_story("Это сцена один. Это сцена два. Это сцена три.", 3)
        print(f"  ✓ Разбиение на сцены: {len(scenes)} сцен")
        
        # Тест улучшения промпта
        enhanced = processor.enhance_prompt("Кот сидит на окне", "Cinematic")
        print(f"  ✓ Промпт улучшен: {enhanced[:50]}...")
        
        return True
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция тестирования"""
    print("="*60)
    print("  Тестирование StoryForge AI")
    print("="*60)
    
    tests = [
        test_imports,
        test_directories,
        test_model_download,
        test_app,
        test_generation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n  ✗ Критическая ошибка в {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print("  РЕЗУЛЬТАТЫ")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nПройдено: {passed}/{total} тестов")
    
    if passed == total:
        print("\n✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("\nДля запуска приложения:")
        print("  python app.py")
        print("\nИли:")
        print("  start.bat")
        return 0
    else:
        print("\n✗ Некоторые тесты не пройдены")
        print("\nУстановите зависимости:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
