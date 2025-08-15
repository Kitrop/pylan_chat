@echo off
chcp 65001 >nul
echo 🚀 Сборка LANChat для Windows...

set SCRIPT_DIR=%~dp0
pushd %SCRIPT_DIR%

REM Установка зависимостей для сборки
echo 📦 Установка зависимостей...
python -m pip install -r requirements_build.txt
if errorlevel 1 (
	echo ❌ Ошибка установки зависимостей
	popd
	exit /b 1
)

REM Запуск сборки
echo 🔧 Запуск сборки...
python build_windows.py
set EXIT_CODE=%ERRORLEVEL%

popd

if %EXIT_CODE% NEQ 0 (
	echo ❌ Ошибка сборки (%EXIT_CODE%)
	exit /b %EXIT_CODE%
)

echo 🎉 Сборка завершена! Файлы: dist\
exit /b 0
