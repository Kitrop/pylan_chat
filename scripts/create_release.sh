#!/bin/bash

# LANChat Release Creator для Linux/macOS
# Использование: ./create_release.sh [patch|minor|major] [message]

set -e

echo "🚀 LANChat Release Creator"
echo "================================"

# Проверяем аргументы
if [ $# -eq 0 ]; then
    echo "❌ Ошибка: Укажите тип версии"
    echo ""
    echo "Использование:"
    echo "  $0 patch    - Патч релиз (1.0.0 → 1.0.1)"
    echo "  $0 minor    - Минорный релиз (1.0.0 → 1.1.0)"
    echo "  $0 major    - Мажорный релиз (1.0.0 → 2.0.0)"
    echo ""
    echo "Примеры:"
    echo "  $0 patch \"Исправлена ошибка\""
    echo "  $0 minor \"Добавлена новая функция\""
    echo "  $0 major \"Полное обновление\""
    exit 1
fi

VERSION_TYPE=$1
MESSAGE=${2:-"Release"}

echo "📋 Тип версии: $VERSION_TYPE"
echo "💬 Сообщение: $MESSAGE"
echo ""

# Проверяем, что Python установлен
if ! command -v python3 &> /dev/null; then
    echo "❌ Ошибка: Python3 не найден"
    echo "Установите Python3:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  macOS: brew install python3"
    exit 1
fi

# Проверяем, что мы в правильной директории
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Ошибка: pyproject.toml не найден"
    echo "Запустите скрипт из корневой директории проекта"
    exit 1
fi

# Проверяем, что git установлен
if ! command -v git &> /dev/null; then
    echo "❌ Ошибка: Git не найден"
    echo "Установите Git:"
    echo "  Ubuntu/Debian: sudo apt install git"
    echo "  macOS: brew install git"
    exit 1
fi

echo "✅ Проверки пройдены"
echo ""

# Запускаем Python скрипт
echo "🔄 Создаем релиз..."
python3 scripts/create_release.py "$VERSION_TYPE" -m "$MESSAGE"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Ошибка при создании релиза"
    echo "Проверьте логи выше"
    exit 1
fi

echo ""
echo "🎉 Релиз создан успешно!"
echo ""
echo "💡 Следующие шаги:"
echo "  1. Проверьте GitHub Actions"
echo "  2. Дождитесь завершения сборки"
echo "  3. Скачайте релиз с GitHub"
echo ""
echo "🔗 GitHub Actions: https://github.com/your-username/lanchat/actions"
echo "📦 Releases: https://github.com/your-username/lanchat/releases"
