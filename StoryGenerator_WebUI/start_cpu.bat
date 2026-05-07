@echo off
chcp 65001 >nul
title StoryForge AI - CPU Mode

echo ============================================
echo    StoryForge AI v2.0.0 - CPU MODE
echo    Оптимизировано для работы без GPU
echo ============================================
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Пожалуйста, установите Python 3.9+
    pause
    exit /b 1
)

:: Активация окружения
call venv\Scripts\activate.bat 2>nul
if errorlevel 1 (
    echo [INFO] Создание окружения...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -q -r requirements.txt
)

:: Проверка CPU
echo [INFO] Режим: CPU (оптимизировано)
echo [INFO] Рекомендуется: 8GB+ RAM
echo.

:: Установка CPU-версии PyTorch если нужно
python -c "import torch; assert not torch.cuda.is_available()" 2>nul
if errorlevel 1 (
    echo [INFO] Установка CPU-версии PyTorch...
    pip uninstall -y torch torchvision torchaudio 2>nul
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    echo [OK] Установлена CPU-версия
echo.
)

echo [INFO] Запуск в CPU-режиме...
echo [INFO] Разрешение будет автоматически уменьшено до 256x256
echo [INFO] Ожидаемое время: 2-3 минуты на изображение
echo.
echo Откройте браузер: http://localhost:7860
echo.
echo Нажмите Ctrl+C для остановки
echo.

set CUDA_VISIBLE_DEVICES=-1
python app.py --cpu

pause
