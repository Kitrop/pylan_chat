#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LANChat GUI Launcher
Простой запускатель для графического интерфейса LANChat
"""

import sys
import os

def main():
    """Главная функция запуска GUI"""
    try:
        # Проверка наличия необходимых модулей
        import tkinter
        print("✅ Tkinter доступен")
        
        # Запуск GUI
        from gui import main as gui_main
        print("🚀 Запуск графического интерфейса LANChat...")
        gui_main()
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("\nУбедитесь, что установлены все необходимые зависимости:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка запуска GUI: {e}")
        print("\nПопробуйте запустить в командной строке:")
        print("python main.py --gui")
        sys.exit(1)

if __name__ == "__main__":
    main()
