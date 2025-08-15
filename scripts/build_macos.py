#!/usr/bin/env python3
"""
Сборка LANChat для macOS (PyInstaller)
Запуск: python scripts/build_macos.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def build():
    if sys.platform != "darwin":
        print("❌ Скрипт предназначен для macOS")
        return 1

    # Определяем корень проекта и переходим в него
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    os.chdir(project_root)

    print("🚀 Сборка LANChat для macOS...")
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
    icon_icns = project_root / "icon.icns"
    add_icon = [f"--icon={icon_icns}"] if icon_icns.exists() else []

    uploads_dir = project_root / "uploads"
    # Для Unix синтаксис add-data: src:dest
    add_data = [
        f"--add-data={uploads_dir}:uploads"] if uploads_dir.exists() else []

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
        "--clean",
        "run_gui.py",
    ]

    print("📦 Запуск PyInstaller:")
    print(" ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
        bin_path = project_root / "dist" / "LANChat"
        if bin_path.exists():
            print(f"✅ Готово: {bin_path}")
        else:
            print("⚠️ Сборка завершилась без ошибок, но файл не найден")
            return 1
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка сборки: {e}")
        return e.returncode


if __name__ == "__main__":
    sys.exit(build())
