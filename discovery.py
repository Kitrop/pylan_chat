import argparse
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo
import socket
import uuid
import signal
import sys
from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()
discovery_service = None  # Глобальная переменная для хранения экземпляра сервиса

class DiscoveryService:
    def __init__(self, service_name, port, local_ip):
        self.zeroconf = Zeroconf()
        self.service_name = service_name
        self.port = port
        self.local_ip = local_ip
        self._devices = []  # Использовать префикс подчеркивания для приватных переменных
        self.info = None
        self.browser = None
        # Добавить определение типа сервиса
        self.service_type = "_lanchat._tcp.local."

    @property
    def devices(self):
        """Получить список обнаруженных устройств"""
        return self._devices

    def get_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]
        
    def start_advertising(self):
        """Начать рекламу этого сервиса в сети"""
        try:
            self.info = ServiceInfo(
                self.service_type,
                f"{self.service_name}.{self.service_type}",
                addresses=[socket.inet_aton(self.local_ip)],  # Использовать self.local_ip вместо
                port=self.port,
                properties={'version': '1.0'},
            )
            self.zeroconf.register_service(self.info)
            print(f"✅ Сервис зарегистрирован: {self.service_name} ({self.local_ip}:{self.port})")
        except Exception as e:
            print(f"❌ Регистрация сервиса не удалась: {e}")

    def start_discovery(self):
        """Начать обнаружение других сервисов"""
        try:
            self.browser = ServiceBrowser(self.zeroconf, self.service_type, self)
            print("✅ Обнаружение сервисов запущено")
        except Exception as e:
            print(f"❌ Запуск обнаружения сервисов не удался: {e}")
        
    def add_service(self, zeroconf, type_, name):
        info = zeroconf.get_service_info(type_, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            port = info.port
            
            # Фильтрация адресов локальной связи и локальных адресов
            if ip.startswith("169.254.") or (ip == self.local_ip and port == self.port):
                return
                
            device = {
                "name": name,
                "ip": ip,
                "port": port
            }
            if device not in self._devices:
                self._devices.append(device)
                print(f"[DISCOVERY] Новое устройство присоединилось: {name} ({ip}:{port})")
                print(f"[STATUS] Текущее количество обнаруженных устройств: {len(self._devices)}")

    def remove_service(self, zeroconf, type_, name):
        self._devices = [d for d in self._devices if d["name"] != name]
        print(f"[DISCOVERY] Устройство покинуло: {name}")
        print(f"[STATUS] Текущее количество обнаруженных устройств: {len(self._devices)}")

    def update_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            updated_device = {
                "name": name.split(".")[0],
                "ip": socket.inet_ntoa(info.addresses[0]),
                "port": info.port
            }
            for device in self.devices:
                if device["name"] == updated_device["name"]:
                    device.update(updated_device)
                    self.add_device(updated_device["name"], updated_device["ip"], updated_device["port"])
                    print(f"[UPDATE] Информация об устройстве обновлена: {device['name']} ({device['ip']}:{device['port']})")
                    break

    def unregister_service(self):
        self.zeroconf.unregister_service(self.service_info)
        self.zeroconf.close()
        print(f"[UNREGISTER] Локальный сервис отменен: {self.service_name}")

    def stop(self):
        """Остановить обнаружение сервисов и широковещательную передачу"""
        self._is_running = False
        if self.browser:
            self.browser.cancel()
        if self.info:
            self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()
        print("✅ Обнаружение сервисов остановлено")

    def add_device(self, name: str, ip: str, port: int):
        """Добавить обнаруженное устройство"""
        self.discovered_devices[name] = {
            "name": name,
            "ip": ip,
            "port": port
        }
        
    def remove_device(self, name: str):
        """Удалить устройство, когда оно покидает"""
        if name in self.discovered_devices:
            del self.discovered_devices[name]

def signal_handler(signal, frame, discovery):
    print("\n[EXIT] Выход из программы...")
    discovery.unregister_service()
    sys.exit(0)

def initialize_discovery(service: DiscoveryService):
    """Инициализировать сервис обнаружения для API endpoints"""
    global discovery_service
    discovery_service = service

if __name__ == "__main__":
    # Парсинг аргументов командной строки (необязательно)
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, help="Порт сервиса (необязательно)")
    args = parser.parse_args()

    # Запуск сервиса
    discovery = DiscoveryService(args.port)
    discovery.start_advertising()
    discovery.start_discovery()

    # Регистрация обработчика сигналов
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, discovery))
    signal.signal(signal.SIGTERM, lambda sig, frame: signal_handler(sig, frame, discovery))

    print("Нажмите Ctrl+C или закройте терминал для выхода...")
    input("Нажмите Enter для выхода...\n")
    discovery.unregister_service()

# Добавить FastAPI роутер для обнаружения устройств
@router.get("/devices")
async def get_devices():
    """Получить все обнаруженные устройства"""
    if discovery_service is None:
        return {"error": "Сервис обнаружения не инициализирован"}
    return discovery_service.devices