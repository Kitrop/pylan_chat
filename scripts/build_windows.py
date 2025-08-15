#!/usr/bin/env python3
"""
Сборка LANChat для Windows (PyInstaller)
Запуск: python scripts/build_windows.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def build():
    # Определяем корень проекта и переходим в него
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    os.chdir(project_root)

    print("🚀 Сборка LANChat для Windows...")
    print(f"📂 Корень проекта: {project_root}")

    # Проверяем/ставим PyInstaller
    try:
        import PyInstaller  # noqa: F401
        print("✓ PyInstaller найден")
    except Exception:
        print("⬇️ Устанавливаю PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip",
                       "install", "pyinstaller"], check=True)

    # Очистка
    for dir_name in ("dist", "build"):
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)

    # Опциональные ресурсы
    icon_path = project_root / "icon.ico"
    add_icon = [f"--icon={icon_path}"] if icon_path.exists() else []

    uploads_dir = project_root / "uploads"
    # Для Windows синтаксис add-data: src;dest
    add_data = [
        f"--add-data={uploads_dir};uploads"] if uploads_dir.exists() else []

    # Команда
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=LANChat",
        *add_icon,
        *add_data,
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.scrolledtext",
        "--hidden-import=discovery",
        "--hidden-import=msg_server",
        "--hidden-import=file_tsf",
        "--exclude=PySide6",            # Исключаем PySide6 для избежания конфликта с PyQt5
        "--clean",
        "run_gui.py",
    ]

    print("📦 Запуск PyInstaller:")
    print(" ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
        exe_path = project_root / "dist" / "LANChat.exe"
        if exe_path.exists():
            print(f"✅ Готово: {exe_path}")
        else:
            print("⚠️ Сборка завершилась без ошибок, но файл не найден")
            return 1
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка сборки: {e}")
        return e.returncode


if __name__ == "__main__":
    sys.exit(build())
