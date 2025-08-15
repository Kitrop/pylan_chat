import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import asyncio
import json
import os
from datetime import datetime
import queue
import shutil
import mimetypes
from pathlib import Path


# Импорт существующих модулей
from discovery import DiscoveryService, initialize_discovery
from msg_server import MessageBroadcaster
import requests
import socket


class LANChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LANChat - Чат в локальной сети")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')

        # Инициализация переменных
        self.username = tk.StringVar(value="Пользователь")
        self.message_var = tk.StringVar()
        self.chat_messages = []
        self.devices = []
        self.is_chat_active = False
        self.message_queue = queue.Queue()

        # Инициализация сервисов
        self.discovery_service = None
        self.message_broadcaster = None

        # Переменные для файлов
        self.uploads_folder = Path("uploads")
        self.uploads_folder.mkdir(exist_ok=True)
        self.file_messages = {}  # Словарь для хранения информации о файлах в чате

        # Создание интерфейса
        self.create_widgets()
        self.setup_styles()

        # Проверка инициализации
        if not hasattr(self, 'messages_text') or not self.messages_text:
            print("Ошибка: виджет messages_text не был создан")
            messagebox.showerror("Ошибка", "Не удалось создать виджет чата")
            return

        # Запуск сервисов
        self.start_services()

        # Запуск обновления GUI
        self.update_gui()

    def setup_styles(self):
        """Настройка стилей для современного вида"""
        style = ttk.Style()
        style.theme_use('clam')

        # Настройка цветов
        style.configure('Title.TLabel', font=(
            'Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=(
            'Arial', 12, 'bold'), foreground='#34495e')
        style.configure('Info.TLabel', font=(
            'Arial', 10), foreground='#7f8c8d')

        # Настройка кнопок
        style.configure('Action.TButton', font=(
            'Arial', 10, 'bold'), padding=5)
        style.configure('Success.TButton', font=(
            'Arial', 10, 'bold'), padding=5)
        style.configure('Warning.TButton', font=(
            'Arial', 10, 'bold'), padding=5)
        style.configure('Info.TButton', font=('Arial', 10, 'bold'), padding=5)

    def create_widgets(self):
        """Создание виджетов интерфейса"""
        # Главный заголовок
        title_frame = tk.Frame(self.root, bg='#3498db', height=60)
        title_frame.pack(fill='x', padx=10, pady=5)
        title_frame.pack_propagate(False)

        title_label = tk.Label(title_frame, text="LANChat", font=('Arial', 24, 'bold'),
                               fg='white', bg='#3498db')
        title_label.pack(pady=15)

        # Основной контейнер
        main_container = ttk.PanedWindow(self.root, orient='horizontal')
        main_container.pack(fill='both', expand=True, padx=10, pady=5)

        # Левая панель - Чат и сообщения
        self.create_chat_panel(main_container)

        # Правая панель - Устройства и функции
        self.create_control_panel(main_container)

        # Статусная строка
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                              relief='sunken', anchor='w', bg='#ecf0f1')
        status_bar.pack(side='bottom', fill='x')

    def create_chat_panel(self, parent):
        """Создание панели чата"""
        chat_frame = ttk.Frame(parent)
        parent.add(chat_frame, weight=2)

        # Заголовок чата
        chat_header = tk.Frame(chat_frame, bg='#ecf0f1', height=40)
        chat_header.pack(fill='x', padx=5, pady=5)
        chat_header.pack_propagate(False)

        tk.Label(chat_header, text="Чат", font=('Arial', 14, 'bold'),
                 bg='#ecf0f1').pack(side='left', padx=10, pady=8)

        # Кнопки управления чатом
        self.chat_btn = ttk.Button(chat_header, text="Присоединиться",
                                   style='Action.TButton', command=self.toggle_chat)
        self.chat_btn.pack(side='right', padx=10, pady=5)

        # Кнопка очистки чата
        clear_btn = ttk.Button(chat_header, text="Очистить",
                               style='Warning.TButton', command=self.clear_chat)
        clear_btn.pack(side='right', padx=5, pady=5)

        # Кнопка обновления интерфейса
        refresh_btn = ttk.Button(chat_header, text="Обновить",
                                 style='Action.TButton', command=self.force_update)
        refresh_btn.pack(side='right', padx=5, pady=5)

        # Индикатор состояния сервисов (лампочка)
        self.status_indicator = tk.Label(chat_header, text="●", font=('Arial', 16, 'bold'),
                                         fg='red', bg='#ecf0f1')
        self.status_indicator.pack(side='right', padx=5, pady=5)

        # Подсказка для индикатора
        self.status_indicator.bind('<Enter>', self.show_status_tooltip)
        self.status_indicator.bind('<Leave>', self.hide_status_tooltip)

        # Кнопка списка файлов
        files_list_btn = ttk.Button(chat_header, text="📁 Файлы",
                                    style='Success.TButton', command=self.show_files_list)
        files_list_btn.pack(side='right', padx=5, pady=5)

        # Область сообщений
        messages_frame = tk.Frame(chat_frame)
        messages_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Список сообщений
        self.messages_text = scrolledtext.ScrolledText(messages_frame, wrap='word',
                                                       font=('Arial', 10), bg='white')
        self.messages_text.pack(fill='both', expand=True)

        # Панель ввода сообщения
        input_frame = tk.Frame(chat_frame, bg='#ecf0f1', height=60)
        input_frame.pack(fill='x', padx=5, pady=5)
        input_frame.pack_propagate(False)

        self.message_entry = tk.Entry(input_frame, textvariable=self.message_var,
                                      font=('Arial', 11), relief='solid', bd=1)
        self.message_entry.pack(side='left', fill='x',
                                expand=True, padx=(10, 5), pady=15)

        # Кнопка для выбора файла
        file_btn = ttk.Button(input_frame, text="📎", style='Action.TButton',
                              command=self.browse_file_for_chat)
        file_btn.pack(side='left', padx=2, pady=15)

        send_btn = ttk.Button(input_frame, text="Отправить", style='Action.TButton',
                              command=self.send_message)
        send_btn.pack(side='right', padx=(5, 10), pady=15)

        # Привязка Enter для отправки
        self.message_entry.bind('<Return>', lambda e: self.send_message())

    def create_control_panel(self, parent):
        """Создание панели управления"""
        control_frame = ttk.Frame(parent)
        parent.add(control_frame, weight=1)

        # Вкладки для разных функций
        notebook = ttk.Notebook(control_frame)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Вкладка устройств
        self.create_devices_tab(notebook)

        # Вкладка настроек
        self.create_settings_tab(notebook)

    def create_devices_tab(self, notebook):
        """Создание вкладки устройств"""
        devices_frame = ttk.Frame(notebook)
        notebook.add(devices_frame, text="Устройства")

        # Заголовок
        tk.Label(devices_frame, text="Обнаруженные устройства",
                 font=('Arial', 12, 'bold'), bg='#ecf0f1').pack(pady=10)

        # Список устройств
        self.devices_tree = ttk.Treeview(
            devices_frame, columns=('IP', 'Port'), show='tree headings')
        self.devices_tree.heading('#0', text='Имя устройства')
        self.devices_tree.heading('IP', text='IP адрес')
        self.devices_tree.heading('Port', text='Порт')
        self.devices_tree.column('#0', width=150)
        self.devices_tree.column('IP', width=120)
        self.devices_tree.column('Port', width=80)
        self.devices_tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Кнопки управления
        btn_frame = tk.Frame(devices_frame)
        btn_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(btn_frame, text="Обновить", style='Action.TButton',
                   command=self.refresh_devices).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Подключиться", style='Success.TButton',
                   command=self.connect_to_device).pack(side='right', padx=5)

    def create_settings_tab(self, notebook):
        """Создание вкладки настроек"""
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Настройки")

        # Настройки пользователя
        user_frame = tk.LabelFrame(settings_frame, text="Пользователь",
                                   font=('Arial', 11, 'bold'), bg='#ecf0f1')
        user_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(user_frame, text="Имя пользователя:",
                 bg='#ecf0f1').pack(anchor='w', padx=10, pady=5)
        username_entry = tk.Entry(
            user_frame, textvariable=self.username, width=25)
        username_entry.pack(padx=10, pady=5)

        # Информация о системе
        info_frame = tk.LabelFrame(settings_frame, text="Информация о системе",
                                   font=('Arial', 11, 'bold'), bg='#ecf0f1')
        info_frame.pack(fill='x', padx=10, pady=10)

        self.local_ip_var = tk.StringVar()
        tk.Label(info_frame, text="Локальный IP:", bg='#ecf0f1').pack(
            anchor='w', padx=10, pady=2)
        tk.Label(info_frame, textvariable=self.local_ip_var,
                 bg='#ecf0f1', fg='#2980b9').pack(anchor='w', padx=20, pady=2)

        self.port_var = tk.StringVar()
        tk.Label(info_frame, text="Порт:", bg='#ecf0f1').pack(
            anchor='w', padx=10, pady=2)
        tk.Label(info_frame, textvariable=self.port_var, bg='#ecf0f1',
                 fg='#2980b9').pack(anchor='w', padx=20, pady=2)

    def start_services(self):
        """Запуск сервисов в фоновом режиме"""
        def run_services():
            try:
                # Получение локального IP
                local_ip = self.get_local_ip()
                if local_ip:
                    self.local_ip_var.set(local_ip)

                    # Получение свободного порта
                    port = self.get_free_port()
                    self.port_var.set(str(port))

                    # Инициализация сервиса обнаружения
                    self.discovery_service = DiscoveryService(
                        f"LANChat_{port}",
                        port,
                        local_ip
                    )
                    initialize_discovery(self.discovery_service)
                    self.discovery_service.start_advertising()
                    self.discovery_service.start_discovery()

                    # Инициализация широковещателя сообщений
                    self.message_broadcaster = MessageBroadcaster()

                    self.status_var.set("Сервисы запущены")
                    print("Все сервисы успешно запущены")

                    # Запуск обновления устройств
                    self.refresh_devices()

                    # Обновляем индикатор состояния
                    self.update_status_indicator()

                else:
                    self.status_var.set(
                        "Ошибка: не удалось получить локальный IP")
                    print("Ошибка: не удалось получить локальный IP")

            except Exception as e:
                error_msg = f"Ошибка запуска сервисов: {e}"
                self.status_var.set(error_msg)
                print(error_msg)
                messagebox.showerror(
                    "Ошибка", f"Не удалось запустить сервисы: {e}")

        # Запуск в отдельном потоке
        service_thread = threading.Thread(target=run_services, daemon=True)
        service_thread.start()

    def get_local_ip(self):
        """Получение локального IP"""
        try:
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            for ip in ip_list:
                if ip.startswith("192.168."):
                    return ip
            return ip_list[0] if ip_list else None
        except:
            return None

    def get_free_port(self):
        """Получение свободного порта"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def toggle_chat(self):
        """Переключение состояния чата"""
        if not self.is_chat_active:
            self.start_chat()
        else:
            self.stop_chat()

    def start_chat(self):
        """Запуск чата"""
        if not self.username.get().strip():
            messagebox.showwarning(
                "Предупреждение", "Пожалуйста, введите имя пользователя")
            return

        self.is_chat_active = True
        self.chat_btn.config(text="Отключиться")
        self.status_var.set("Чат активен | Сообщений: 0")

        # Обновляем индикатор состояния
        self.update_status_indicator()

        # Запуск получения сообщений
        def receive_messages():
            def handle_message(message, addr):
                if message.get('username') != self.username.get():
                    self.message_queue.put(message)

            try:
                self.message_broadcaster.start(handle_message)

                # Отправка уведомления о входе
                self.message_broadcaster.broadcast({
                    "username": "system",
                    "message": f"{self.username.get()} вошел в чат"
                })

                print("Поток получения сообщений запущен")
            except Exception as e:
                print(f"Ошибка запуска потока получения сообщений: {e}")
                self.status_var.set(f"Ошибка запуска чата: {e}")

        chat_thread = threading.Thread(target=receive_messages, daemon=True)
        chat_thread.start()

        # Добавляем системное сообщение в очередь для корректной обработки
        self.message_queue.put({
            "username": "system",
            "message": f"Вы присоединились к чату как {self.username.get()}"
        })

    def stop_chat(self):
        """Остановка чата"""
        self.is_chat_active = False
        self.chat_btn.config(text="Присоединиться")
        self.status_var.set("Чат отключен")

        # Обновляем индикатор состояния
        self.update_status_indicator()

        if self.message_broadcaster:
            # Отправка уведомления о выходе
            self.message_broadcaster.broadcast({
                "username": "system",
                "message": f"{self.username.get()} покинул чат"
            })
            self.message_broadcaster.stop()

        # Добавляем системное сообщение в очередь для корректной обработки
        self.message_queue.put({
            "username": "system",
            "message": "Вы покинули чат"
        })

    def send_message(self):
        """Отправка сообщения"""
        message = self.message_var.get().strip()
        if not message:
            return

        if not self.is_chat_active:
            messagebox.showwarning(
                "Предупреждение", "Сначала присоединитесь к чату")
            return

        # Отправка сообщения
        if self.message_broadcaster:
            self.message_broadcaster.broadcast({
                "username": self.username.get(),
                "message": message
            })

        # Добавление в локальный чат
        self.add_message(self.username.get(), message)
        self.message_var.set("")

    def add_message(self, username, message):
        """Добавление сообщения в чат"""
        try:
            timestamp = datetime.now().strftime("%H:%M")
            formatted_message = f"[{timestamp}] {username}: {message}\n"

            # Проверка, что виджет доступен
            if hasattr(self, 'messages_text') and self.messages_text:
                self.messages_text.insert('end', formatted_message)
                self.messages_text.see('end')

                # Ограничение количества сообщений (удаляем старые, если больше 1000 строк)
                lines = int(self.messages_text.index('end-1c').split('.')[0])
                if lines > 1000:
                    # Удаляем первые 200 строк, оставляя 800
                    self.messages_text.delete('1.0', '200.0')
            else:
                print(f"Ошибка: виджет messages_text недоступен")
        except Exception as e:
            print(f"Ошибка добавления сообщения: {e}")
            # Попытка восстановления
            try:
                self.force_update()
            except:
                pass

    def add_system_message(self, message):
        """Добавление системного сообщения"""
        try:
            # Проверка на дублирование последнего системного сообщения
            if hasattr(self, 'messages_text') and self.messages_text:
                last_line = self.messages_text.get(
                    'end-2c linestart', 'end-1c')
                if last_line.strip() == f"Система: {message}":
                    return  # Не добавляем дублирующее сообщение

                timestamp = datetime.now().strftime("%H:%M")
                formatted_message = f"[{timestamp}] Система: {message}\n"

                self.messages_text.insert('end', formatted_message, 'system')
                self.messages_text.tag_config('system', foreground='#7f8c8d')
                self.messages_text.see('end')

                # Ограничение количества сообщений (удаляем старые, если больше 1000 строк)
                lines = int(self.messages_text.index('end-1c').split('.')[0])
                if lines > 1000:
                    # Удаляем первые 200 строк, оставляя 800
                    self.messages_text.delete('1.0', '200.0')
            else:
                print(f"Ошибка: виджет messages_text недоступен")
        except Exception as e:
            print(f"Ошибка добавления системного сообщения: {e}")
            # Попытка восстановления
            try:
                self.force_update()
            except:
                pass

    def refresh_devices(self):
        """Обновление списка устройств"""
        if not self.discovery_service:
            return

        # Очистка списка
        for item in self.devices_tree.get_children():
            self.devices_tree.delete(item)

        # Добавление устройств
        devices = self.discovery_service.devices
        for device in devices:
            self.devices_tree.insert('', 'end', text=device['name'],
                                     values=(device['ip'], device['port']))

        self.status_var.set(f"Найдено устройств: {len(devices)}")

    def connect_to_device(self):
        """Подключение к выбранному устройству"""
        selection = self.devices_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Предупреждение", "Выберите устройство для подключения")
            return

        device = self.devices_tree.item(selection[0])
        device_name = device['text']
        device_ip = device['values'][0]
        device_port = device['values'][1]

        messagebox.showinfo(
            "Подключение", f"Подключение к {device_name} ({device_ip}:{device_port})")

    def clear_chat(self):
        """Очистка чата"""
        try:
            if hasattr(self, 'messages_text') and self.messages_text:
                self.messages_text.delete('1.0', 'end')
                # Добавляем системное сообщение напрямую
                timestamp = datetime.now().strftime("%H:%M")
                formatted_message = f"[{timestamp}] Система: Чат очищен\n"
                self.messages_text.insert('end', formatted_message, 'system')
                self.messages_text.tag_config('system', foreground='#7f8c8d')
                self.messages_text.see('end')
            else:
                print(f"Ошибка: виджет messages_text недоступен")
        except Exception as e:
            print(f"Ошибка очистки чата: {e}")
            # Попытка восстановления
            try:
                self.force_update()
            except:
                pass

    def add_test_messages_to_queue(self):
        """Добавление тестовых сообщений в очередь для тестирования"""
        try:
            import time
            timestamp = time.strftime("%H:%M:%S")

            # Добавляем несколько тестовых сообщений в очередь
            test_messages = [
                {"username": "Тест1", "message": f"Тестовое сообщение 1 в {timestamp}"},
                {"username": "Тест2", "message": f"Тестовое сообщение 2 в {timestamp}"},
                {"username": "Тест3", "message": f"Тестовое сообщение 3 в {timestamp}"},
                {"username": "system",
                    "message": f"Тестовое системное сообщение в {timestamp}"},
                {"username": "Тест4", "message": f"Тестовое сообщение 4 в {timestamp}"},
                {"username": "Тест5", "message": f"Тестовое сообщение 5 в {timestamp}"}
            ]

            for msg in test_messages:
                self.message_queue.put(msg)

            print(
                f"Добавлено {len(test_messages)} тестовых сообщений в очередь")
            self.status_var.set(
                f"Добавлено {len(test_messages)} тестовых сообщений")

        except Exception as e:
            error_msg = f"Ошибка добавления тестовых сообщений: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def diagnose_chat_issues(self):
        """Диагностика проблем с отображением сообщений"""
        try:
            print("=== ДИАГНОСТИКА ЧАТА ===")

            # Проверка состояния виджета чата
            if hasattr(self, 'messages_text') and self.messages_text:
                print("✓ Виджет чата доступен")

                # Проверка количества строк
                try:
                    lines = int(self.messages_text.index(
                        'end-1c').split('.')[0])
                    print(f"✓ Количество строк в чате: {lines}")
                except:
                    print("✗ Не удалось получить количество строк")

                # Проверка содержимого
                try:
                    content = self.messages_text.get('1.0', 'end-1c')
                    if content.strip():
                        print(f"✓ Содержимое чата: {len(content)} символов")
                        # Показываем последние 100 символов
                        last_content = content[-100:] if len(
                            content) > 100 else content
                        print(f"  Последние символы: {repr(last_content)}")
                    else:
                        print("✗ Чат пуст")
                except:
                    print("✗ Не удалось получить содержимое чата")
            else:
                print("✗ Виджет чата недоступен")

            # Проверка состояния очереди сообщений
            try:
                queue_size = self.message_queue.qsize()
                print(f"✓ Размер очереди сообщений: {queue_size}")
            except:
                print("✗ Не удалось проверить очередь сообщений")

            # Проверка состояния чата
            print(
                f"✓ Состояние чата: {'активен' if self.is_chat_active else 'неактивен'}")

            # Проверка сервисов
            print(
                f"✓ Discovery сервис: {'доступен' if self.discovery_service else 'недоступен'}")
            print(
                f"✓ Broadcaster: {'доступен' if self.message_broadcaster else 'недоступен'}")

            print("=== КОНЕЦ ДИАГНОСТИКИ ===")

            # Показываем результат в статусе
            self.status_var.set("Диагностика завершена - проверьте консоль")

        except Exception as e:
            error_msg = f"Ошибка диагностики: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def force_refresh_chat(self):
        """Принудительное обновление интерфейса чата"""
        try:
            # Принудительное обновление виджета чата
            if hasattr(self, 'messages_text') and self.messages_text:
                self.messages_text.update_idletasks()
                self.messages_text.update()

                # Прокрутка к последнему сообщению
                self.messages_text.see('end')

                # Обновление счетчика сообщений
                lines = int(self.messages_text.index('end-1c').split('.')[0])
                self.status_var.set(f"Чат обновлен | Сообщений: {lines}")

                print(
                    f"Интерфейс чата принудительно обновлен. Сообщений: {lines}")
            else:
                print("Виджет чата недоступен")

        except Exception as e:
            error_msg = f"Ошибка обновления чата: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def start_queue_monitoring(self):
        """Запуск мониторинга очереди сообщений"""
        try:
            if not hasattr(self, 'queue_monitoring_active'):
                self.queue_monitoring_active = False

            if not self.queue_monitoring_active:
                self.queue_monitoring_active = True

                def monitor_queue():
                    while self.queue_monitoring_active:
                        try:
                            queue_size = self.message_queue.qsize()
                            if queue_size > 0:
                                print(
                                    f"Мониторинг: в очереди {queue_size} сообщений")

                                # Обновляем статус каждые 5 секунд
                                if hasattr(self, 'status_var'):
                                    self.status_var.set(
                                        f"Мониторинг: {queue_size} сообщений в очереди")

                            import time
                            time.sleep(5)  # Проверяем каждые 5 секунд

                        except Exception as e:
                            print(f"Ошибка мониторинга очереди: {e}")
                            break

                monitor_thread = threading.Thread(
                    target=monitor_queue, daemon=True)
                monitor_thread.start()

                print("Мониторинг очереди сообщений запущен")
                self.status_var.set("Мониторинг очереди запущен")
            else:
                self.queue_monitoring_active = False
                print("Мониторинг очереди сообщений остановлен")
                self.status_var.set("Мониторинг очереди остановлен")

        except Exception as e:
            print(f"Ошибка запуска мониторинга очереди: {e}")

    def force_refresh_devices(self):
        """Принудительное обновление списка устройств"""
        try:
            if self.discovery_service:
                # Очистка списка
                for item in self.devices_tree.get_children():
                    self.devices_tree.delete(item)

                # Принудительное обновление
                self.discovery_service.refresh_devices()

                # Добавление устройств
                devices = self.discovery_service.devices
                for device in devices:
                    self.devices_tree.insert('', 'end', text=device['name'],
                                             values=(device['ip'], device['port']))

                self.status_var.set(f"Устройства обновлены: {len(devices)}")
                print(
                    f"Список устройств принудительно обновлен: {len(devices)} устройств")
            else:
                self.status_var.set("Сервис обнаружения недоступен")
                print("Сервис обнаружения недоступен")

        except Exception as e:
            error_msg = f"Ошибка обновления устройств: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def restart_services(self):
        """Перезапуск сервисов"""
        try:
            # Остановка существующих сервисов
            if self.discovery_service:
                self.discovery_service.stop()
                self.discovery_service = None

            if self.message_broadcaster:
                self.message_broadcaster.stop()
                self.message_broadcaster = None

            # Очистка состояния
            self.is_chat_active = False
            self.chat_btn.config(text="Присоединиться")

            # Перезапуск сервисов
            self.start_services()

            print("Сервисы перезапущены")
            self.status_var.set("Сервисы перезапущены")

            # Обновляем индикатор состояния
            self.update_status_indicator()

        except Exception as e:
            error_msg = f"Ошибка перезапуска сервисов: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def update_status_indicator(self):
        """Обновление индикатора состояния сервисов"""
        try:
            # Определяем общее состояние
            discovery_ok = self.discovery_service is not None
            broadcaster_ok = self.message_broadcaster is not None
            chat_ok = self.is_chat_active

            # Устанавливаем цвет лампочки
            if discovery_ok and broadcaster_ok and chat_ok:
                # Все сервисы работают - зеленый
                self.status_indicator.config(fg='green')
                self.status_indicator.config(text="●")
            elif discovery_ok and broadcaster_ok:
                # Основные сервисы работают, но чат неактивен - желтый
                self.status_indicator.config(fg='orange')
                self.status_indicator.config(text="●")
            else:
                # Проблемы с сервисами - красный
                self.status_indicator.config(fg='red')
                self.status_indicator.config(text="●")

        except Exception as e:
            print(f"Ошибка обновления индикатора состояния: {e}")

    def show_status_tooltip(self, event):
        """Показать подсказку о состоянии сервисов"""
        try:
            discovery_ok = self.discovery_service is not None
            broadcaster_ok = self.message_broadcaster is not None
            chat_ok = self.is_chat_active

            status_text = f"Discovery: {'✓' if discovery_ok else '✗'}\n"
            status_text += f"Broadcaster: {'✓' if broadcaster_ok else '✗'}\n"
            status_text += f"Chat: {'✓' if chat_ok else '✗'}"

            self.status_var.set(status_text)
        except:
            pass

    def hide_status_tooltip(self, event):
        """Скрыть подсказку о состоянии сервисов"""
        try:
            # Возвращаем обычный статус
            if self.is_chat_active:
                try:
                    lines = int(self.messages_text.index(
                        'end-1c').split('.')[0])
                    files_count = len(self.file_messages)
                    self.status_var.set(
                        f"Чат активен | Сообщений: {lines} | Файлов: {files_count}")
                except:
                    self.status_var.set("Чат активен")
            else:
                self.status_var.set("Чат отключен")
        except:
            pass

    def check_queue_status(self):
        """Проверка состояния очереди сообщений"""
        try:
            queue_size = self.message_queue.qsize()
            print(f"Размер очереди сообщений: {queue_size}")

            # Показываем информацию в статусе
            if hasattr(self, 'status_var'):
                self.status_var.set(f"Размер очереди: {queue_size}")

            return queue_size
        except Exception as e:
            print(f"Ошибка проверки очереди: {e}")
            return 0

    def test_messages(self):
        """Тестирование отображения сообщений"""
        try:
            # Добавляем тестовые сообщения
            self.add_message("Тест", "Это тестовое сообщение")
            self.add_system_message("Тестовое системное сообщение")
            self.add_message("Пользователь", "Еще одно тестовое сообщение")
            print("Тестовые сообщения добавлены")
        except Exception as e:
            print(f"Ошибка тестирования: {e}")

    def force_update(self):
        """Принудительное обновление интерфейса"""
        try:
            self.root.update_idletasks()
            self.root.update()

            # Принудительное обновление виджета чата
            if hasattr(self, 'messages_text') and self.messages_text:
                self.messages_text.update_idletasks()
                self.messages_text.update()

            print("Интерфейс принудительно обновлен")
        except Exception as e:
            print(f"Ошибка принудительного обновления: {e}")

    def update_gui(self):
        """Обновление GUI"""
        # Проверка доступности виджетов
        if not hasattr(self, 'messages_text') or not self.messages_text:
            # Если виджет недоступен, пропускаем обновление
            self.root.after(100, self.update_gui)
            return

        # Обработка сообщений из очереди
        try:
            message_count = 0
            while True:
                message = self.message_queue.get_nowait()
                username = message.get('username', 'Неизвестно')
                message_text = message.get('message', '')

                # Проверяем, является ли сообщение файловым
                if 'file_info' in message:
                    self.handle_incoming_file(username, message['file_info'])
                elif username == 'system':
                    self.add_system_message(message_text)
                else:
                    self.add_message(username, message_text)
                message_count += 1

                # Ограничиваем количество сообщений за один цикл обновления
                if message_count > 50:
                    break

        except queue.Empty:
            pass
        except Exception as e:
            print(f"Ошибка обработки сообщения: {e}")
            # Попытка восстановления
            try:
                self.status_var.set(f"Ошибка обработки сообщения: {e}")
            except:
                pass

        # Обновление счетчика сообщений в статусе
        if self.is_chat_active:
            try:
                lines = int(self.messages_text.index('end-1c').split('.')[0])
                files_count = len(self.file_messages)
                self.status_var.set(
                    f"Чат активен | Сообщений: {lines} | Файлов: {files_count}")
            except:
                pass

        # Обновляем индикатор состояния каждые 10 циклов (примерно раз в секунду)
        if not hasattr(self, '_update_counter'):
            self._update_counter = 0
        self._update_counter += 1

        if self._update_counter >= 10:
            self.update_status_indicator()
            self._update_counter = 0

        # Обновление каждые 100мс
        self.root.after(100, self.update_gui)

    def debug_refresh(self):
        """Отладочное обновление интерфейса с подробным логированием"""
        try:
            print("=== ОТЛАДОЧНОЕ ОБНОВЛЕНИЕ ===")

            # Логируем состояние всех компонентов
            print(f"1. Состояние чата: {self.is_chat_active}")
            print(f"2. Размер очереди: {self.message_queue.qsize()}")
            print(f"3. Discovery сервис: {self.discovery_service is not None}")
            print(f"4. Broadcaster: {self.message_broadcaster is not None}")

            # Проверяем виджет чата
            if hasattr(self, 'messages_text') and self.messages_text:
                try:
                    lines = int(self.messages_text.index(
                        'end-1c').split('.')[0])
                    print(f"6. Строк в чате: {lines}")

                    # Проверяем содержимое
                    content = self.messages_text.get('1.0', 'end-1c')
                    if content.strip():
                        print(f"7. Символов в чате: {len(content)}")
                        # Показываем последние 200 символов
                        last_content = content[-200:] if len(
                            content) > 200 else content
                        print(f"8. Последние символы: {repr(last_content)}")
                    else:
                        print("7. Чат пуст")
                        print("8. Нет содержимого для анализа")
                except Exception as e:
                    print(f"6. Ошибка анализа чата: {e}")
                    print("7. Нет данных")
                    print("8. Нет данных")
            else:
                print("6. Виджет чата недоступен")
                print("7. Нет данных")
                print("8. Нет данных")

            # Проверяем состояние потоков
            print(f"9. Активных потоков: {threading.active_count()}")

            # Выполняем обновление
            print("10. Выполняем обновление...")
            self.force_refresh_all()

            # Проверяем результат
            if hasattr(self, 'messages_text') and self.messages_text:
                try:
                    lines_after = int(
                        self.messages_text.index('end-1c').split('.')[0])
                    print(f"11. Строк после обновления: {lines_after}")
                except:
                    print("11. Не удалось получить количество строк после обновления")
            else:
                print("11. Виджет чата недоступен после обновления")

            print("=== ОТЛАДОЧНОЕ ОБНОВЛЕНИЕ ЗАВЕРШЕНО ===")

            # Показываем результат в статусе
            self.status_var.set("Отладка завершена - проверьте консоль")

        except Exception as e:
            error_msg = f"Ошибка отладочного обновления: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def recovery_refresh(self):
        """Восстановительное обновление интерфейса"""
        try:
            print("Восстановительное обновление интерфейса...")

            # Проверяем и восстанавливаем основные компоненты
            issues_found = []

            # Проверка виджета чата
            if not hasattr(self, 'messages_text') or not self.messages_text:
                issues_found.append("Виджет чата недоступен")
                print("Восстанавливаем виджет чата...")
                # Здесь можно добавить логику восстановления
            else:
                print("Виджет чата доступен")

            # Проверка очереди сообщений
            try:
                queue_size = self.message_queue.qsize()
                if queue_size > 100:
                    issues_found.append(f"Очередь переполнена: {queue_size}")
                    print("Очищаем переполненную очередь...")
                    # Очищаем очередь, оставляя только последние 50 сообщений
                    temp_queue = queue.Queue()
                    count = 0
                    while not self.message_queue.empty() and count < 50:
                        try:
                            msg = self.message_queue.get_nowait()
                            temp_queue.put(msg)
                            count += 1
                        except:
                            break
                    self.message_queue = temp_queue
                    print(f"Очередь очищена, оставлено {count} сообщений")
            except:
                issues_found.append("Ошибка проверки очереди")

            # Проверка состояния чата
            if self.is_chat_active and not self.message_broadcaster:
                issues_found.append("Broadcaster недоступен при активном чате")
                print("Восстанавливаем broadcaster...")
                try:
                    self.message_broadcaster = MessageBroadcaster()
                    print("Broadcaster восстановлен")
                except Exception as e:
                    print(f"Не удалось восстановить broadcaster: {e}")

            # Выполняем полное обновление
            self.force_refresh_all()

            # Показываем результат
            if issues_found:
                issues_text = "; ".join(issues_found)
                self.status_var.set(
                    f"Восстановление завершено. Проблемы: {issues_text}")
                print(
                    f"Восстановление завершено. Найдены проблемы: {issues_text}")
            else:
                self.status_var.set(
                    "Восстановление завершено. Проблем не найдено")
                print("Восстановление завершено. Проблем не найдено")

        except Exception as e:
            error_msg = f"Ошибка восстановительного обновления: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def smart_refresh(self):
        """Умное обновление интерфейса с проверкой состояния"""
        try:
            print("Умное обновление интерфейса...")

            # Проверяем состояние чата
            if self.is_chat_active:
                print("Чат активен - выполняем полное обновление")
                self.force_refresh_all()
            else:
                print("Чат неактивен - выполняем базовое обновление")
                self.root.update_idletasks()
                self.root.update()

            # Проверяем размер очереди сообщений
            try:
                queue_size = self.message_queue.qsize()
                if queue_size > 0:
                    print(
                        f"В очереди {queue_size} сообщений - принудительно обрабатываем")
                    # Принудительно обрабатываем сообщения
                    self.update_gui()
                else:
                    print("Очередь пуста")
            except:
                print("Не удалось проверить очередь сообщений")

            # Проверяем состояние виджета чата
            if hasattr(self, 'messages_text') and self.messages_text:
                try:
                    lines = int(self.messages_text.index(
                        'end-1c').split('.')[0])
                    print(f"В чате {lines} строк")
                    self.status_var.set(
                        f"Умное обновление завершено | Строк: {lines}")
                except:
                    print("Не удалось получить количество строк")
                    self.status_var.set("Умное обновление завершено")
            else:
                print("Виджет чата недоступен")
                self.status_var.set("Умное обновление завершено")

            print("Умное обновление завершено")

        except Exception as e:
            error_msg = f"Ошибка умного обновления: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def progress_refresh(self, steps=10, step_delay=100):
        """Принудительное обновление интерфейса с прогресс-баром"""
        try:
            print(f"Прогрессивное обновление: {steps} шагов по {step_delay}мс")
            self.status_var.set(f"Прогресс: 0/{steps}")

            def step_update(step):
                if step < steps:
                    try:
                        # Обновляем конкретный элемент
                        if step == 0:
                            # Обновление основного окна
                            self.root.update_idletasks()
                            self.root.update()
                        elif step == 1:
                            # Обновление виджета чата
                            if hasattr(self, 'messages_text') and self.messages_text:
                                self.messages_text.update_idletasks()
                                self.messages_text.update()
                        elif step == 2:
                            # Обновление дерева устройств
                            if hasattr(self, 'devices_tree') and self.devices_tree:
                                self.devices_tree.update_idletasks()
                                self.devices_tree.update()
                        elif step == 3:
                            # Обновление всех фреймов
                            for child in self.root.winfo_children():
                                try:
                                    child.update_idletasks()
                                    child.update()
                                except:
                                    pass
                        elif step == 4:
                            # Обновление счетчика сообщений
                            if self.is_chat_active and hasattr(self, 'messages_text') and self.messages_text:
                                try:
                                    lines = int(self.messages_text.index(
                                        'end-1c').split('.')[0])
                                    self.status_var.set(
                                        f"Прогресс: {step+1}/{steps} | Сообщений: {lines}")
                                except:
                                    self.status_var.set(
                                        f"Прогресс: {step+1}/{steps}")
                            else:
                                self.status_var.set(
                                    f"Прогресс: {step+1}/{steps}")
                        else:
                            # Общие обновления
                            self.root.update_idletasks()
                            self.root.update()
                            self.status_var.set(f"Прогресс: {step+1}/{steps}")

                        # Планируем следующий шаг
                        self.root.after(
                            step_delay, lambda: step_update(step + 1))

                    except Exception as e:
                        print(f"Ошибка на шаге {step}: {e}")
                        # Продолжаем со следующим шагом
                        self.root.after(
                            step_delay, lambda: step_update(step + 1))
                else:
                    # Завершение
                    self.status_var.set("Прогрессивное обновление завершено")
                    print("Прогрессивное обновление завершено")

            # Запускаем первый шаг
            step_update(0)

        except Exception as e:
            error_msg = f"Ошибка прогрессивного обновления: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def start_continuous_refresh(self, interval_ms=500):
        """Запуск непрерывного обновления интерфейса"""
        try:
            if not hasattr(self, 'continuous_refresh_active'):
                self.continuous_refresh_active = False

            if not self.continuous_refresh_active:
                self.continuous_refresh_active = True

                def continuous_update():
                    if self.continuous_refresh_active:
                        try:
                            self.force_refresh_all()
                            # Планируем следующее обновление
                            self.root.after(interval_ms, continuous_update)
                        except Exception as e:
                            print(f"Ошибка непрерывного обновления: {e}")
                            self.continuous_refresh_active = False

                # Запускаем первое обновление
                self.root.after(interval_ms, continuous_update)

                print(
                    f"Непрерывное обновление запущено с интервалом {interval_ms}мс")
                self.status_var.set(f"Непрерывное обновление: {interval_ms}мс")
            else:
                self.continuous_refresh_active = False
                print("Непрерывное обновление остановлено")
                self.status_var.set("Непрерывное обновление остановлено")

        except Exception as e:
            error_msg = f"Ошибка запуска непрерывного обновления: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def delayed_refresh(self, delay_ms=1000):
        """Принудительное обновление интерфейса с задержкой"""
        try:
            print(f"Запланировано обновление интерфейса через {delay_ms}мс...")
            self.status_var.set(f"Обновление через {delay_ms//1000}с...")

            def delayed_update():
                try:
                    self.force_refresh_all()
                    print("Отложенное обновление завершено")
                except Exception as e:
                    print(f"Ошибка отложенного обновления: {e}")

            # Запуск отложенного обновления
            self.root.after(delay_ms, delayed_update)

        except Exception as e:
            error_msg = f"Ошибка планирования обновления: {e}"
            print(error_msg)
            self.status_var.set(error_msg)

    def browse_file_for_chat(self):
        """Выбор файла для отправки в чат"""
        filename = filedialog.askopenfilename(
            title="Выберите файл для отправки в чат")
        if filename:
            self.add_file_message(filename)

    def add_file_message(self, file_path):
        """Добавление сообщения о файле в чат"""
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_type = mimetypes.guess_type(file_path)[0] or "Неизвестный тип"

            # Копируем файл в папку uploads
            dest_path = self.uploads_folder / file_name
            # Не копируем, если файл уже в папке uploads
            if file_path != str(dest_path):
                shutil.copy2(file_path, dest_path)

            # Создаем уникальный ID для файла
            file_id = f"file_{len(self.file_messages)}_{int(datetime.now().timestamp())}"
            self.file_messages[file_id] = {
                'name': file_name,
                'path': str(dest_path),
                'size': file_size,
                'type': file_type,
                'timestamp': datetime.now()
            }

            # Добавляем сообщение о файле в чат
            timestamp = datetime.now().strftime("%H:%M")
            formatted_message = f"[{timestamp}] 📎 {self.username.get()} отправил файл: {file_name} ({file_size} байт, {file_type})\n"

            if hasattr(self, 'messages_text') and self.messages_text:
                # Вставляем сообщение
                start_pos = self.messages_text.index('end-1c')
                self.messages_text.insert('end', formatted_message)

                # Добавляем тег для кликабельности файла
                file_start = f"{start_pos} linestart"
                file_end = f"{start_pos} lineend"
                self.messages_text.tag_add(file_id, file_start, file_end)
                self.messages_text.tag_config(
                    file_id, foreground='#2980b9', underline=True)
                self.messages_text.tag_bind(
                    file_id, '<Button-1>', lambda e, fname=file_name: self.download_file_from_chat(fname))
                self.messages_text.tag_bind(
                    file_id, '<Enter>', lambda e, fname=file_name: self.show_file_tooltip(e, fname))
                self.messages_text.tag_bind(
                    file_id, '<Leave>', lambda e: self.hide_file_tooltip())

                self.messages_text.see('end')

            # Отправляем файловое сообщение другим пользователям
            if self.message_broadcaster and self.is_chat_active:
                self.message_broadcaster.broadcast({
                    "username": self.username.get(),
                    "message": f"отправил файл: {file_name}",
                    "file_info": {
                        'name': file_name,
                        'size': file_size,
                        'type': file_type
                    }
                })

            print(f"Файл {file_name} добавлен в чат")

        except Exception as e:
            error_msg = f"Ошибка добавления файла: {e}"
            print(error_msg)
            messagebox.showerror("Ошибка", error_msg)

    def handle_incoming_file(self, username, file_info):
        """Обработка входящего файла от другого пользователя"""
        try:
            file_name = file_info.get('name', 'Неизвестный файл')
            file_size = file_info.get('size', 0)
            file_type = file_info.get('type', 'Неизвестный тип')

            timestamp = datetime.now().strftime("%H:%M")
            formatted_message = f"[{timestamp}] 📥 {username} отправил файл: {file_name} ({file_size} байт, {file_type})\n"

            # Проверка, что виджет доступен
            if hasattr(self, 'messages_text') and self.messages_text:
                # Вставляем сообщение
                start_pos = self.messages_text.index('end-1c')
                self.messages_text.insert('end', formatted_message)

                # Добавляем тег для файла
                file_id = f"incoming_file_{len(self.file_messages)}_{int(datetime.now().timestamp())}"
                self.file_messages[file_id] = {
                    'name': file_name,
                    'path': str(self.uploads_folder / file_name),
                    'size': file_size,
                    'type': file_type,
                    'timestamp': datetime.now()
                }

                # Добавляем тег для кликабельности файла
                file_start = f"{start_pos} linestart"
                file_end = f"{start_pos} lineend"
                self.messages_text.tag_add(file_id, file_start, file_end)
                self.messages_text.tag_config(
                    file_id, foreground='#2980b9', underline=True)
                self.messages_text.tag_bind(
                    file_id, '<Button-1>', lambda e, fname=file_name: self.download_file_from_chat(fname))
                self.messages_text.tag_bind(
                    file_id, '<Enter>', lambda e, fname=file_name: self.show_file_tooltip(e, fname))
                self.messages_text.tag_bind(
                    file_id, '<Leave>', lambda e: self.hide_file_tooltip())

                # Прокручиваем к новому сообщению
                self.messages_text.see('end')

                print(f"Входящий файл {file_name} обработан")

        except Exception as e:
            print(f"Ошибка обработки входящего файла: {e}")

    def download_file_from_chat(self, file_name):
        """Скачивание файла из чата"""
        try:
            # Ищем файл в папке uploads
            file_path = self.uploads_folder / file_name
            if file_path.exists():
                # Открываем диалог сохранения
                save_path = filedialog.asksaveasfilename(
                    title="Сохранить файл как",
                    initialfile=file_name,
                    defaultextension=file_path.suffix
                )
                if save_path:
                    shutil.copy2(file_path, save_path)
                    messagebox.showinfo("Успех", f"Файл {file_name} сохранен")
            else:
                messagebox.showerror("Ошибка", f"Файл {file_name} не найден")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скачать файл: {e}")

    def show_file_tooltip(self, event, file_name):
        """Показать подсказку для файла"""
        try:
            # Показываем подсказку о том, что файл можно скачать
            tooltip_text = f"Кликните для скачивания файла: {file_name}"
            self.status_var.set(tooltip_text)
        except:
            pass

    def hide_file_tooltip(self):
        """Скрыть подсказку для файла"""
        try:
            # Возвращаем обычный статус
            if self.is_chat_active:
                try:
                    lines = int(self.messages_text.index(
                        'end-1c').split('.')[0])
                    files_count = len(self.file_messages)
                    self.status_var.set(
                        f"Чат активен | Сообщений: {lines} | Файлов: {files_count}")
                except:
                    self.status_var.set("Чат активен")
            else:
                self.status_var.set("Чат отключен")
        except:
            pass

    def show_files_list(self):
        """Отображение списка всех файлов в чате"""
        try:
            if not self.file_messages:
                messagebox.showinfo("Файлы", "В чате нет файлов")
                return

            # Создаем окно со списком файлов
            files_window = tk.Toplevel(self.root)
            files_window.title("Файлы в чате")
            files_window.geometry("600x400")
            files_window.configure(bg='#f0f0f0')

            # Заголовок
            header = tk.Label(files_window, text="Файлы в чате",
                              font=('Arial', 16, 'bold'), bg='#f0f0f1')
            header.pack(pady=10)

            # Список файлов
            files_frame = tk.Frame(files_window, bg='#f0f0f0')
            files_frame.pack(fill='both', expand=True, padx=20, pady=10)

            # Создаем Treeview для файлов
            columns = ('Имя', 'Размер', 'Тип', 'Дата')
            files_tree = ttk.Treeview(
                files_frame, columns=columns, show='headings', height=15)

            # Настройка колонок
            files_tree.heading('Имя', text='Имя файла')
            files_tree.heading('Размер', text='Размер')
            files_tree.heading('Тип', text='Тип файла')
            files_tree.heading('Дата', text='Дата получения')

            files_tree.column('Имя', width=200)
            files_tree.column('Размер', width=100)
            files_tree.column('Тип', width=150)
            files_tree.column('Дата', width=120)

            # Добавляем файлы в список
            for file_id, file_info in self.file_messages.items():
                size_str = f"{file_info['size']} байт"
                date_str = file_info['timestamp'].strftime("%d.%m %H:%M")
                files_tree.insert('', 'end', values=(
                    file_info['name'],
                    size_str,
                    file_info['type'],
                    date_str
                ))

            files_tree.pack(fill='both', expand=True)

            # Кнопки управления
            btn_frame = tk.Frame(files_window, bg='#f0f0f0')
            btn_frame.pack(fill='x', padx=20, pady=10)

            ttk.Button(btn_frame, text="Скачать выбранный", style='Success.TButton',
                       command=lambda: self.download_selected_file(files_tree)).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Открыть папку", style='Action.TButton',
                       command=self.open_uploads_folder).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Закрыть", style='Warning.TButton',
                       command=files_window.destroy).pack(side='right', padx=5)

            # Привязываем двойной клик для скачивания
            files_tree.bind(
                '<Double-1>', lambda e: self.download_selected_file(files_tree))

        except Exception as e:
            error_msg = f"Ошибка отображения списка файлов: {e}"
            print(error_msg)
            messagebox.showerror("Ошибка", error_msg)

    def download_selected_file(self, files_tree):
        """Скачивание выбранного файла из списка"""
        try:
            selection = files_tree.selection()
            if not selection:
                messagebox.showwarning(
                    "Предупреждение", "Выберите файл для скачивания")
                return

            # Получаем имя файла из выбранной строки
            file_name = files_tree.item(selection[0])['values'][0]
            self.download_file_from_chat(file_name)

        except Exception as e:
            error_msg = f"Ошибка скачивания файла: {e}"
            print(error_msg)
            messagebox.showerror("Ошибка", error_msg)

    def open_uploads_folder(self):
        """Открытие папки с загруженными файлами"""
        try:
            import subprocess
            import platform

            if platform.system() == "Windows":
                subprocess.run(['explorer', str(self.uploads_folder)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(['open', str(self.uploads_folder)])
            else:  # Linux
                subprocess.run(['xdg-open', str(self.uploads_folder)])

        except Exception as e:
            print(f"Ошибка открытия папки: {e}")
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")

    def force_refresh_all(self):
        """Принудительное обновление всех элементов интерфейса"""
        try:
            print("Принудительное обновление всех элементов интерфейса...")

            # Обновление основного окна
            self.root.update_idletasks()
            self.root.update()

            # Обновление виджета чата
            if hasattr(self, 'messages_text') and self.messages_text:
                self.messages_text.update_idletasks()
                self.messages_text.update()
                self.messages_text.see('end')

            # Обновление дерева устройств
            if hasattr(self, 'devices_tree') and self.devices_tree:
                self.devices_tree.update_idletasks()
                self.devices_tree.update()

            # Обновление всех фреймов
            for child in self.root.winfo_children():
                try:
                    child.update_idletasks()
                    child.update()
                except:
                    pass

            # Обновление счетчика сообщений
            if self.is_chat_active and hasattr(self, 'messages_text') and self.messages_text:
                try:
                    lines = int(self.messages_text.index(
                        'end-1c').split('.')[0])
                    self.status_var.set(f"Все обновлено | Сообщений: {lines}")
                except:
                    self.status_var.set("Все обновлено")
            else:
                self.status_var.set("Все обновлено")

            print("Все элементы интерфейса обновлены")

        except Exception as e:
            error_msg = f"Ошибка обновления интерфейса: {e}"
            print(error_msg)
            self.status_var.set(error_msg)


def main():
    """Главная функция для запуска GUI"""
    try:
        root = tk.Tk()
        app = LANChatGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Ошибка запуска GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
