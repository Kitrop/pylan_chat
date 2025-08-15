@echo off
REM LANChat Release Creator для Windows
REM Использование: create_release.bat [patch|minor|major] [message]

setlocal enabledelayedexpansion

echo 🚀 LANChat Release Creator
echo ================================

if "%1"=="" (
    echo ❌ Ошибка: Укажите тип версии
    echo.
    echo Использование:
    echo   create_release.bat patch    - Патч релиз (1.0.0 ^>^> 1.0.1)
    echo   create_release.bat minor    - Минорный релиз (1.0.0 ^>^> 1.1.0)
    echo   create_release.bat major    - Мажорный релиз (1.0.0 ^>^> 2.0.0)
    echo.
    echo Примеры:
    echo   create_release.bat patch "Исправлена ошибка"
    echo   create_release.bat minor "Добавлена новая функция"
    echo   create_release.bat major "Полное обновление"
    exit /b 1
)

set VERSION_TYPE=%1
set MESSAGE=%2

if "%MESSAGE%"=="" (
    set MESSAGE=Release
)

echo 📋 Тип версии: %VERSION_TYPE%
echo 💬 Сообщение: %MESSAGE%
echo.

REM Проверяем, что Python установлен
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ошибка: Python не найден
    echo Установите Python и добавьте его в PATH
    exit /b 1
)

REM Проверяем, что мы в правильной директории
if not exist "pyproject.toml" (
    echo ❌ Ошибка: pyproject.toml не найден
    echo Запустите скрипт из корневой директории проекта
    exit /b 1
)

REM Проверяем, что git установлен
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ошибка: Git не найден
    echo Установите Git и добавьте его в PATH
    exit /b 1
)

echo ✅ Проверки пройдены
echo.

REM Запускаем Python скрипт
echo 🔄 Создаем релиз...
python scripts/create_release.py %VERSION_TYPE% -m "%MESSAGE%"

if errorlevel 1 (
    echo.
    echo ❌ Ошибка при создании релиза
    echo Проверьте логи выше
    exit /b 1
)

echo.
echo 🎉 Релиз создан успешно!
echo.
echo 💡 Следующие шаги:
echo   1. Проверьте GitHub Actions
echo   2. Дождитесь завершения сборки
echo   3. Скачайте релиз с GitHub
echo.
echo 🔗 GitHub Actions: https://github.com/your-username/lanchat/actions
echo 📦 Releases: https://github.com/your-username/lanchat/releases

pause
