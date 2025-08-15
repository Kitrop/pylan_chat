#!/usr/bin/env python3
"""
Универсальная сборка LANChat для текущей ОС
Запуск: python scripts/build_all.py
"""

import platform
import subprocess
import sys
from pathlib import Path


def main():
    script_dir = Path(__file__).resolve().parent
    current = platform.system().lower()
    if current == "windows":
        build_script = script_dir / "build_windows.py"
    elif current == "darwin":
        build_script = script_dir / "build_macos.py"
    elif current == "linux":
        build_script = script_dir / "build_linux.py"
    else:
        print(f"❌ Неподдерживаемая ОС: {current}")
        return 1

    return subprocess.call([sys.executable, str(build_script)])


if __name__ == "__main__":
    sys.exit(main())
