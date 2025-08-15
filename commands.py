import click
import requests
import websockets
import asyncio
import json
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import print as rprint
import pyperclip
from rich.prompt import Prompt
import threading
from msg_server import MessageBroadcaster
import re

console = Console()


class CommandHandler:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.ws_base_url = f"ws://{host}:{port}"
        self.chat_task = None
        self.username = None
        try:
            self.message_broadcaster = MessageBroadcaster()  # Не нужно указывать порт
        except Exception as e:
            rprint(
                f"[red]Не удалось инициализировать широковещатель сообщений: {e}[/red]")
            raise

    async def ws_handle_chat(self):
        """Обработка сообщений чата"""
        uri = f"{self.ws_base_url}/message/ws"
        async with websockets.connect(uri) as ws:
            rprint("[green]✓[/green] Подключен к чат-комнате")
            # Задача для получения сообщений

            async def receive_messages():
                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        rprint(
                            f"\n[bold blue]{data['username']}[/bold blue]: {data['message']}")
                        print(">>> ", end='', flush=True)
                    except Exception as e:
                        rprint(f"[red]Ошибка получения сообщения: {e}[/red]")
                        break

            # Задача для отправки сообщений
            async def send_messages():
                while True:
                    try:
                        message = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: input(">>> ")
                        )
                        if message.lower() in ['/quit', '/exit']:
                            break
                        # Включение имени пользователя при отправке сообщения
                        await ws.send_json({
                            "username": self.username,
                            "message": message
                        })
                    except Exception as e:
                        rprint(f"[red]Ошибка отправки сообщения: {e}[/red]")
                        break

            try:
                # Отправка уведомления о входе в чат-комнату
                await ws.send_json({
                    "username": "system",
                    "message": f"{self.username} вошел в чат-комнату"
                })

                # Параллельный запуск отправки и получения сообщений
                await asyncio.gather(
                    receive_messages(),
                    send_messages()
                )
            except Exception as e:
                rprint(f"[red]Ошибка подключения к чат-комнате: {e}[/red]")
            finally:
                # Отправка уведомления о выходе из чат-комнаты
                try:
                    await ws.send_json({
                        "username": "system",
                        "message": f"{self.username} покинул чат-комнату"
                    })
                except:
                    pass

    def boardcast_start_chat(self):
        """Запуск клиента чата"""
        if not self.username:
            self.username = Prompt.ask("Введите ваше имя пользователя")

        def handle_message(message: dict, addr):
            username = message.get('username', 'Неизвестно')
            msg = message.get('message', '')
            if username != self.username:
                rprint(f"\n[bold blue]{username}[/bold blue]: {msg}")
                print(">>> ", end='', flush=True)

        try:
            # Запуск широковещателя сообщений
            self.message_broadcaster.start(handle_message)

            # Отправка уведомления о входе
            self.message_broadcaster.broadcast({
                "username": "system",
                "message": f"{self.username} вошел в чат"
            })

            rprint(
                "[green]✓[/green] Чат запущен! Введите сообщения (Ctrl+C для выхода)")

            # Основной цикл чата
            while True:
                try:
                    message = input(">>> ")
                    if message.lower() in ['/quit', '/exit']:
                        break

                    # Отправка сообщения
                    self.message_broadcaster.broadcast({
                        "username": self.username,
                        "message": message
                    })

                except KeyboardInterrupt:
                    break

        except Exception as e:
            rprint(f"[red]Ошибка запуска чата: {e}[/red]")
        finally:
            # Отправка уведомления о выходе
            try:
                self.message_broadcaster.broadcast({
                    "username": "system",
                    "message": f"{self.username} покинул чат"
                })
                self.message_broadcaster.stop()
            except:
                pass
            rprint("[yellow]Чат завершен[/yellow]")

    def show_online_devices(self):
        """Показать список онлайн устройств"""
        try:
            response = requests.get(f"{self.base_url}/discovery/devices")
            if response.status_code == 200:
                devices = response.json()
                if devices:
                    table = Table(title="Онлайн устройства")
                    table.add_column("Имя устройства")
                    table.add_column("IP адрес")
                    table.add_column("Порт")

                    for device in devices:
                        table.add_row(
                            device['name'],
                            device['ip'],
                            str(device['port'])
                        )
                    console.print(table)
                else:
                    rprint(
                        "[yellow]В настоящее время не обнаружено других устройств[/yellow]")
            else:
                rprint(
                    f"[red]Не удалось получить список устройств: {response.status_code}[/red]")
        except Exception as e:
            rprint(f"[red]Ошибка получения списка устройств: {e}[/red]")

    def get_target_device(self, param: str = None) -> tuple:
        """Получение IP и порта целевого устройства
        param: может быть номером устройства (-n) или форматом IP:порт
        return: (ip, port) или None
        """
        try:
            response = requests.get(f"{self.base_url}/discovery/devices")
            if response.status_code != 200:
                rprint(
                    f"[red]Не удалось получить список устройств: {response.status_code}[/red]")
                return None

            devices = response.json()
            if not devices:
                rprint(
                    "[yellow]В настоящее время не обнаружено других устройств[/yellow]")
                return None

            # Автоматический выбор, если только одно устройство
            if len(devices) == 1:
                device = devices[0]
                rprint(
                    f"[green]Автоматически выбран единственный онлайн-устройство: {device['ip']}:{device['port']}[/green]")
                return (device['ip'], device['port'])

            # Обработка параметра номера устройства
            if param and param.startswith('-'):
                try:
                    idx = int(param[1:]) - 1
                    if 0 <= idx < len(devices):
                        device = devices[idx]
                        return (device['ip'], device['port'])
                    else:
                        rprint(
                            f"[red]Номер устройства вне диапазона (1-{len(devices)})[/red]")
                        return None
                except ValueError:
                    pass

            # Показать список устройств для выбора
            table = Table(title="Онлайн устройства")
            table.add_column("Номер")
            table.add_column("Имя устройства")
            table.add_column("IP адрес")
            table.add_column("Порт")

            for idx, device in enumerate(devices, 1):
                table.add_row(
                    str(idx),
                    device['name'],
                    device['ip'],
                    str(device['port'])
                )
            console.print(table)

            choice = Prompt.ask(
                "Выберите номер целевого устройства или введите IP:порт")

            # Обработка ввода
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(devices):
                    device = devices[idx]
                    return (device['ip'], device['port'])
            elif ':' in choice:
                ip, port = choice.split(':')
                return (ip, int(port))

            rprint("[red]Неверный выбор[/red]")
            return None

        except Exception as e:
            rprint(f"[red]Ошибка получения списка устройств: {e}[/red]")
            return None

    def upload_file(self, file_path: str, target_param: str = None):
        """Загрузка файла
        file_path: путь к файлу
        target_param: параметр целевого устройства, может быть номером (-n) или IP:порт
        """
        try:
            target = self.get_target_device(target_param)
            if not target:
                return

            ip, port = target

            with open(file_path, "rb") as file:
                files = {"file": file}
                url = f"http://{ip}:{port}/file/upload"
                response = requests.post(url, files=files)

                if response.status_code == 200:
                    rprint(f"[green]✓[/green] Файл успешно загружен!")
                else:
                    rprint(
                        f"[red]Загрузка файла не удалась: {response.status_code}[/red]")

        except FileNotFoundError:
            rprint(f"[red]Файл не найден: {file_path}[/red]")
        except Exception as e:
            rprint(f"[red]Ошибка загрузки файла: {e}[/red]")

    def download_file(self, file_name: str, source: str):
        """Скачивание файла
        file_name: имя файла для скачивания
        source: IP:порт исходного устройства
        """
        try:
            ip, port = source.split(':')
            url = f"http://{ip}:{port}/file/download/{file_name}"
            response = requests.get(url)

            if response.status_code == 200:
                # Сохранение файла
                with open(file_name, "wb") as f:
                    f.write(response.content)
                rprint(f"[green]✓[/green] Файл {file_name} успешно скачан!")
            else:
                rprint(
                    f"[red]Скачивание файла не удалось: {response.status_code}[/red]")

        except Exception as e:
            rprint(f"[red]Ошибка скачивания файла: {e}[/red]")

    def show_help(self):
        """Показать справочную информацию"""
        help_table = Table(title="Справка по командам")
        help_table.add_column("Команда", style="cyan")
        help_table.add_column("Описание")
        help_table.add_column("Использование")

        commands = [
            ("chat", "Войти в режим группового чата", "/chat"),
            ("devices", "Показать онлайн устройства", "/devices"),
            ("upload", "Загрузить файл", "/upload <путь_к_файлу>"),
            ("download", "Скачать файл", "/download <имя_файла>"),
            ("help", "Показать эту справку", "/help"),
            ("quit", "Выйти из программы", "/quit"),
        ]

        for cmd, desc, usage in commands:
            help_table.add_row(cmd, desc, usage)

        console.print(help_table)
