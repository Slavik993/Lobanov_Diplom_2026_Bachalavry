@echo off
chcp 65001 >nul
title StoryForge AI - Запуск

echo ============================================
echo    StoryForge AI v2.0.0
echo    Генератор изображений по сюжету
echo ============================================
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Пожалуйста, установите Python 3.9+ с https://python.org
    pause
    exit /b 1
)

echo [OK] Python найден:
python --version
echo.

:: Проверка CUDA
python -c "import torch; print(f'[OK] PyTorch {torch.__version__}'); print(f'[INFO] CUDA доступна: {torch.cuda.is_available()}')" 2>nul
if errorlevel 1 (
    echo [INFO] PyTorch не установлен или не проверен
)
echo.

:: Проверка зависимостей
if not exist "venv" (
    echo [INFO] Создание виртуального окружения...
    python -m venv venv
)

echo [INFO] Активация окружения...
call venv\Scripts\activate.bat

:: Установка зависимостей
echo [INFO] Проверка зависимостей...
pip install -q -r requirements.txt

echo.
echo ============================================
echo    Запуск приложения...
echo ============================================
echo.
echo Откройте браузер: http://localhost:7860
echo.
echo Нажмите Ctrl+C для остановки
echo.

python app.py

:: Деактивация при выходе
call venv\Scripts\deactivate.bat

echo.
echo ============================================
echo    Приложение остановлено
echo ============================================
pause
