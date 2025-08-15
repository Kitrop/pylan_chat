#!/bin/bash

set -e

echo "🚀 Сборка LANChat (Unix)"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

# Установка зависимостей
echo "📦 Установка зависимостей..."
python3 -m pip install -r requirements_build.txt

# Определяем ОС
OS=$(uname -s)
if [[ "$OS" == "Darwin" ]]; then
	echo "🍎 macOS"
	python3 build_macos.py
elif [[ "$OS" == "Linux" ]]; then
	echo "🐧 Linux"
	python3 build_linux.py
else
	echo "❌ Неподдерживаемая ОС: $OS"
	exit 1
fi

echo "🎉 Готово! Результаты в dist/"
