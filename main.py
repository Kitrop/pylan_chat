import threading
import argparse
import sys
from discovery import DiscoveryService, router as discovery_router, initialize_discovery
from msg_server import app as message_app
from file_tsf import app as file_app
from fastapi import FastAPI
import uvicorn
import socket
import re

# Объединение нескольких экземпляров FastAPI
main_app = FastAPI()
main_app.mount("/message", message_app)
main_app.mount("/file", file_app)
main_app.include_router(discovery_router, prefix="/discovery")


class ServiceController:
    def __init__(self):
        self.discovery = None
        self.service_port = None

    def run_discovery(self, port=None):
        # Получение локального IP (предпочтительно 192.168.*)
        self.local_ip = self.get_local_ip()
        if not self.local_ip:
            raise RuntimeError(
                "Не удается получить действительный LAN IP, пожалуйста, проверьте сетевое подключение")

        # Динамическое получение порта
        self.service_port = port or self.get_free_port()

        # Инициализация сервиса обнаружения
        self.discovery = DiscoveryService(
            f"LANChat_{self.service_port}",
            self.service_port,
            self.local_ip
        )
        # Инициализация сервиса обнаружения для API endpoints
        initialize_discovery(self.discovery)
        # Запуск сервиса
        self.discovery.start_advertising()
        self.discovery.start_discovery()
        print(f"✅ Сервис запущен на {self.local_ip}:{self.service_port}")

    @staticmethod
    def get_local_ip():
        """Получение локального LAN IP (предпочтительно 192.168.*)"""
        try:
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            for ip in ip_list:
                if ip.startswith("192.168."):
                    return ip
            return ip_list[0] if ip_list else None
        except Exception as e:
            print(f"⚠️ Не удалось получить IP: {e}")
            return None

    @staticmethod
    def get_free_port():
        """Динамическое получение свободного порта"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            if self.discovery:
                self.discovery.stop()
        except Exception as e:
            print(f"⚠️ Ошибка при остановке сервиса обнаружения: {e}")


def run_gui():
    """Запуск графического интерфейса"""
    try:
        from gui import main as gui_main
        print("🚀 Запуск графического интерфейса...")
        gui_main()
    except ImportError as e:
        print(f"❌ Не удалось импортировать GUI модуль: {e}")
        print("Убедитесь, что файл gui.py существует и все зависимости установлены")
    except Exception as e:
        print(f"❌ Ошибка запуска GUI: {e}")


def run_cli():
    """Запуск командной строки"""
    print("""
╔════════════════════════════════════════════════╗
║             LANChat - Инструмент для чата в LAN ║
╚════════════════════════════════════════════════╝

Функции:
1. Сервис сообщений
   - WebSocket связь: ws://<IP>:<PORT>/message/ws
   - Поддержка чата в реальном времени

2. Передача файлов
   - Загрузка файлов: http://<IP>:<PORT>/file/upload
   - Скачивание файлов: http://<IP>:<PORT>/file/download/<filename>

3. Обнаружение устройств
   - Автоматическое обнаружение других устройств LANChat в LAN
   - Отображение статуса онлайн устройств в реальном времени

Использование:
- Нажмите Ctrl+C для выхода
- Используйте параметр --port для указания номера порта
""")
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int,
                        help="Указать порт сервиса (необязательно)")
    args = parser.parse_args()

    # Инициализация контроллера
    controller = ServiceController()

    # Запуск потока сервиса обнаружения
    discovery_thread = threading.Thread(
        target=controller.run_discovery,
        kwargs={"port": args.port}
    )
    discovery_thread.daemon = True
    discovery_thread.start()

    # Ожидание определения порта
    while not controller.service_port:
        pass

    # Запуск основного сервиса
    print(f"🌐 Основной сервис слушает порт: {controller.service_port}")

    # Создание обработчика команд
    from commands import CommandHandler
    cmd_handler = CommandHandler(controller.local_ip, controller.service_port)

    # Запуск сервера
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(
            main_app,
            host="0.0.0.0",
            port=controller.service_port,
            log_level="info"
        )
    )
    server_thread.daemon = True
    server_thread.start()

    # Проверяем, доступен ли stdin (для --windowed режима)
    try:
        import msvcrt
        has_stdin = True
    except ImportError:
        has_stdin = hasattr(sys, 'stdin') and sys.stdin.isatty()

    try:
        if not has_stdin:
            print("⚠️ Консольный ввод недоступен (--windowed режим)")
            print("🌐 Сервер запущен и работает в фоновом режиме")
            print(
                "💡 Для управления используйте веб-интерфейс или запустите без --windowed")

            # Держим программу запущенной
            while True:
                import time
                time.sleep(1)
        else:
            # Интерактивный интерфейс командной строки
            while True:
                cmd = input("\n>>> ").strip()
                if not cmd:
                    continue

                if cmd.startswith("/"):
                    cmd = cmd[1:]

                if cmd == "quit" or cmd == "exit":
                    break
                elif cmd == "help":
                    cmd_handler.show_help()
                elif cmd == "chat":  # Новая команда чата
                    cmd_handler.boardcast_start_chat()
                elif cmd == "devices":
                    cmd_handler.show_online_devices()
                elif cmd.startswith("upload "):
                    parts = cmd.split(" ")
                    if len(parts) > 2:
                        # Обработка случая с параметром устройства
                        file_path = parts[1]
                        target_param = parts[2]
                        cmd_handler.upload_file(file_path, target_param)
                    else:
                        # Обычная загрузка
                        file_path = parts[1]
                        cmd_handler.upload_file(file_path)
                elif cmd.startswith("download "):
                    file_name = cmd.split(" ", 1)[1]
                    source = input("Введите IP:порт исходного устройства: ")
                    cmd_handler.download_file(file_name, source)
                else:
                    print("Неизвестная команда, введите /help для получения справки")

    except KeyboardInterrupt:
        print("\nВыход...")
    finally:
        controller.cleanup()


if __name__ == "__main__":
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(
        description="LANChat - Инструмент для чата в локальной сети")
    parser.add_argument("--port", type=int,
                        help="Указать порт сервиса (необязательно)")
    parser.add_argument("--cli", action="store_true",
                        help="Запустить консольный интерфейс (CLI)")
    args = parser.parse_args()

    if args.cli:
        # Запуск CLI
        run_cli()
    else:
        # По умолчанию запускаем GUI
        run_gui()
