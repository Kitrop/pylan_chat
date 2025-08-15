@echo off
chcp 65001 > nul
title LANChat GUI Launcher

echo ========================================
echo        LANChat - Графический интерфейс
echo ========================================
echo.

echo Проверка Python...
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.7+ с https://python.org
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

echo Проверка Tkinter...
python -c "import tkinter" > nul 2>&1
if errorlevel 1 (
    echo ❌ Tkinter не найден! Переустановите Python с включенным Tkinter
    pause
    exit /b 1
)

echo ✅ Tkinter доступен
echo.

echo 🚀 Запуск графического интерфейса...
echo.

python run_gui.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска GUI
    echo Попробуйте запустить в командной строке: python main.py --gui
    pause
)

