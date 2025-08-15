# 🚀 Сборка LANChat с PyInstaller (scripts/)

Все скрипты сборки находятся в папке `scripts/`.

## Быстрый старт

### Windows
```bat
scripts\build_windows.bat
```
или
```bat
python scripts\build_windows.py
```

### macOS / Linux
```bash
chmod +x scripts/build_unix.sh
./scripts/build_unix.sh
```
или напрямую
```bash
python3 scripts/build_macos.py   # macOS
python3 scripts/build_linux.py   # Linux
```

### Универсально
```bash
python scripts/build_all.py
```

## Установка зависимостей
```bash
pip install -r scripts/requirements_build.txt
```

## Вывод сборки
Результаты появляются в папке `dist/` в корне проекта.

## Примечания
- Иконки указываются автоматически, если в корне есть `icon.ico` (Windows), `icon.icns` (macOS), `icon.png` (Linux).
- Папка `uploads/` добавляется в сборку, если существует.
- Скрипты сами переходят в корень проекта перед запуском PyInstaller.
- Исправлена ошибка `input(): lost sys.stdin` для `--windowed` режима.
- Автоматически исключается PySide6 для избежания конфликтов с PyQt5.

## Устранение проблем

### Ошибка "input(): lost sys.stdin"
- ✅ **Исправлено**: Добавлена проверка доступности stdin в `--windowed` режиме
- Приложение теперь корректно работает в фоновом режиме без консоли

### Конфликт Qt библиотек
- ✅ **Исправлено**: Автоматически исключается PySide6 при обнаружении PyQt5
- Добавлен флаг `--exclude=PySide6` в скрипты сборки
