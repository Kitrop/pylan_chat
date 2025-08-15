#!/bin/bash

# LANChat GUI Launcher для Linux/macOS
# Скрипт запуска графического интерфейса

echo "========================================"
echo "        LANChat - Графический интерфейс"
echo "========================================"
echo

# Проверка Python
echo "Проверка Python..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python не найден! Установите Python 3.7+"
        echo "Ubuntu/Debian: sudo apt-get install python3"
        echo "CentOS/RHEL: sudo yum install python3"
        echo "macOS: brew install python3"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "✅ Python найден: $($PYTHON_CMD --version)"
echo

# Проверка Tkinter
echo "Проверка Tkinter..."
if ! $PYTHON_CMD -c "import tkinter" 2>/dev/null; then
    echo "❌ Tkinter не найден!"
    echo "Установите Tkinter:"
    echo "Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "CentOS/RHEL: sudo yum install tkinter"
    echo "macOS: Tkinter обычно включен в Python"
    exit 1
fi

echo "✅ Tkinter доступен"
echo

# Проверка виртуального окружения
if [ -d "venv" ]; then
    echo "Активация виртуального окружения..."
    source venv/bin/activate
    echo "✅ Виртуальное окружение активировано"
    echo
fi

echo "🚀 Запуск графического интерфейса..."
echo

$PYTHON_CMD run_gui.py

if [ $? -ne 0 ]; then
    echo
    echo "❌ Ошибка запуска GUI"
    echo "Попробуйте запустить в командной строке: $PYTHON_CMD main.py --gui"
fi

