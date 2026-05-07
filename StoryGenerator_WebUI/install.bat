@echo off
chcp 65001 >nul
title StoryForge AI - Установка

echo ============================================
echo    StoryForge AI - Установка
echo ============================================
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo.
    echo Пожалуйста:
    echo 1. Скачайте Python 3.9+ с https://python.org
    echo 2. При установке отметьте "Add Python to PATH"
    echo 3. Перезапустите командную строку
    echo.
    start https://python.org/downloads
    pause
    exit /b 1
)

echo [OK] Python найден:
python --version
echo.

:: Создание виртуального окружения
echo [1/4] Создание виртуального окружения...
if exist "venv" (
    echo [INFO] Окружение уже существует, удаляем...
    rmdir /s /q venv
)
python -m venv venv
echo [OK] Окружение создано
echo.

:: Активация
echo [2/4] Активация окружения...
call venv\Scripts\activate.bat
echo [OK] Окружение активировано
echo.

:: Обновление pip
echo [3/4] Обновление pip...
python -m pip install --upgrade pip
echo [OK] pip обновлен
echo.

:: Установка зависимостей
echo [4/4] Установка зависимостей...
echo [INFO] Это может занять 5-10 минут...
echo.

:: Устанавливаем torch в зависимости от наличия CUDA
python -c "import torch; print('CUDA available')" 2>nul
if %errorlevel% == 0 (
    echo [INFO] Установка PyTorch с CUDA поддержкой...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
) else (
    echo [INFO] Установка PyTorch для CPU...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

:: Остальные зависимости
pip install diffusers transformers accelerate gradio pillow numpy huggingface-hub safetensors

echo.
echo [OK] Все зависимости установлены!
echo.

:: Создание директорий
echo [INFO] Создание рабочих директорий...
if not exist "outputs" mkdir outputs
if not exist "cache" mkdir cache
if not exist "sessions" mkdir sessions
echo [OK] Директории созданы
echo.

:: Проверка установки
echo [INFO] Проверка установки...
python -c "import torch; import gradio; import diffusers; print('[OK] Все библиотеки загружены')"
if %errorlevel% == 0 (
    echo.
    echo ============================================
    echo    УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!
    echo ============================================
    echo.
    echo Чтобы запустить приложение:
    echo   1. Дважды кликните start.bat
    echo   2. Или выполните: python app.py
    echo.
    echo Интерфейс будет доступен по адресу:
    echo   http://localhost:7860
    echo.
) else (
    echo.
    echo [ВНИМАНИЕ] Возникли проблемы при проверке
    echo Попробуйте запустить вручную:
    echo   venv\Scripts\python.exe app.py
)

pause
