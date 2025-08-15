from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import socket
import json
import threading
from typing import Callable, Optional
from rich import print as rprint
import uvicorn

app = FastAPI()

# Разрешить CORS (для будущей интеграции с фронтендом)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageBroadcaster:
    BROADCAST_PORT = 25896  # Фиксированный порт для приема широковещательной передачи

    def __init__(self):
        self.running = False
        self.receive_callback: Optional[Callable] = None
        
        # Создание UDP сокета для приема широковещательной передачи
        self.receive_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receive_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receive_sock.bind(('', self.BROADCAST_PORT))
        
        # Создание UDP сокета для отправки широковещательной передачи
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        rprint(f"[green]✓[/green] Сервис широковещательной передачи сообщений запущен на порту {self.BROADCAST_PORT}")

    def start(self, callback: Callable):
        """Запуск сервиса широковещательной передачи"""
        self.running = True
        self.receive_callback = callback
        
        # Запуск потока приема
        self.receive_thread = threading.Thread(target=self._receive_loop)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
    def stop(self):
        """Остановка сервиса широковещательной передачи"""
        self.running = False
        self.receive_sock.close()
        self.send_sock.close()
        
    def broadcast(self, message: dict):
        """Широковещательная передача сообщения"""
        try:
            data = json.dumps(message).encode('utf-8')
            self.send_sock.sendto(data, ('<broadcast>', self.BROADCAST_PORT))
        except Exception as e:
            rprint(f"[red]Не удалось передать сообщение: {e}[/red]")
            
    def _receive_loop(self):
        """Цикл приема сообщений"""
        while self.running:
            try:
                data, addr = self.receive_sock.recvfrom(4096)
                message = json.loads(data.decode('utf-8'))
                if self.receive_callback:
                    self.receive_callback(message, addr)
            except Exception as e:
                if self.running:
                    rprint(f"[red]Ошибка приема сообщения: {e}[/red]")

broadcaster = MessageBroadcaster()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await broadcaster.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Широковещательная передача полученного сообщения
            await broadcaster.broadcast(data, websocket)
    except Exception as e:
        print(f"Ошибка WebSocket соединения: {e}")
    finally:
        broadcaster.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)