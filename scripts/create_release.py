#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LANChat Release Creator
Автоматическое создание тегов и релизов
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, check=True):
    """Выполнить команду и вернуть результат"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=check
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка выполнения команды: {e}")
        print(f"Команда: {command}")
        print(f"Ошибка: {e.stderr}")
        if check:
            sys.exit(1)
        return None


def get_current_version():
    """Получить текущую версию из pyproject.toml"""
    try:
        with open('pyproject.toml', 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.strip().startswith('version = '):
                    version = line.split('=')[1].strip().strip('"').strip("'")
                    return version
    except FileNotFoundError:
        print("❌ Файл pyproject.toml не найден")
        sys.exit(1)
    return None


def update_version(version_type):
    """Обновить версию в pyproject.toml"""
    current_version = get_current_version()
    if not current_version:
        print("❌ Не удалось получить текущую версию")
        sys.exit(1)
    
    major, minor, patch = map(int, current_version.split('.'))
    
    if version_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif version_type == 'minor':
        minor += 1
        patch = 0
    elif version_type == 'patch':
        patch += 1
    else:
        print(f"❌ Неизвестный тип версии: {version_type}")
        sys.exit(1)
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Обновляем версию в pyproject.toml
    try:
        with open('pyproject.toml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем версию
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('version = '):
                lines[i] = f'version = "{new_version}"'
                break
        
        with open('pyproject.toml', 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Версия обновлена: {current_version} → {new_version}")
        return new_version
    except Exception as e:
        print(f"❌ Ошибка обновления версии: {e}")
        sys.exit(1)


def create_tag(version, message=None):
    """Создать тег"""
    tag_name = f"v{version}"
    
    if not message:
        message = f"Release {version}"
    
    # Проверяем, есть ли несохраненные изменения
    status = run_command("git status --porcelain", check=False)
    if status:
        print("⚠️  Есть несохраненные изменения:")
        print(status)
        response = input("Продолжить? (y/N): ")
        if response.lower() != 'y':
            print("❌ Отменено")
            sys.exit(1)
    
    # Добавляем все изменения
    print("📝 Добавляем изменения...")
    run_command("git add .")
    
    # Коммитим изменения
    print("💾 Создаем коммит...")
    run_command(f'git commit -m "Bump version to {version}"')
    
    # Создаем тег
    print(f"🏷️  Создаем тег {tag_name}...")
    run_command(f'git tag -a {tag_name} -m "{message}"')
    
    # Пушим изменения и тег
    print("🚀 Отправляем изменения...")
    run_command("git push")
    run_command(f"git push origin {tag_name}")
    
    print(f"✅ Тег {tag_name} создан и отправлен!")
    return tag_name


def main():
    parser = argparse.ArgumentParser(
        description="LANChat Release Creator - Автоматическое создание релизов"
    )
    parser.add_argument(
        'version_type',
        choices=['major', 'minor', 'patch'],
        help='Тип обновления версии'
    )
    parser.add_argument(
        '--message', '-m',
        help='Сообщение для тега (опционально)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Показать что будет сделано без выполнения'
    )
    
    args = parser.parse_args()
    
    print("🚀 LANChat Release Creator")
    print("=" * 40)
    
    # Получаем текущую версию
    current_version = get_current_version()
    print(f"📋 Текущая версия: {current_version}")
    
    # Определяем новую версию
    major, minor, patch = map(int, current_version.split('.'))
    if args.version_type == 'major':
        new_version = f"{major + 1}.0.0"
    elif args.version_type == 'minor':
        new_version = f"{major}.{minor + 1}.0"
    else:  # patch
        new_version = f"{major}.{minor}.{patch + 1}"
    
    print(f"🆕 Новая версия: {new_version}")
    
    if args.dry_run:
        print("\n🔍 Режим предварительного просмотра:")
        print(f"  - Обновить версию в pyproject.toml: {current_version} → {new_version}")
        print(f"  - Создать коммит: 'Bump version to {new_version}'")
        print(f"  - Создать тег: v{new_version}")
        if args.message:
            print(f"  - Сообщение тега: {args.message}")
        else:
            print(f"  - Сообщение тега: Release {new_version}")
        print("  - Отправить изменения в репозиторий")
        print("  - Запустить CI/CD pipeline")
        return
    
    # Обновляем версию
    update_version(args.version_type)
    
    # Создаем тег
    tag_name = create_tag(new_version, args.message)
    
    print("\n🎉 Релиз создан успешно!")
    print(f"🏷️  Тег: {tag_name}")
    print("🔄 CI/CD pipeline запущен автоматически")
    print("📦 Релиз будет создан после успешной сборки")
    print("\n💡 Следующие шаги:")
    print("  1. Дождитесь завершения CI/CD pipeline")
    print("  2. Проверьте релиз на GitHub")
    print("  3. Скачайте собранные файлы")


if __name__ == "__main__":
    main()
