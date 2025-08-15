import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import ServiceController


class TestServiceController:
    """Тесты для класса ServiceController"""

    def test_init(self):
        """Тест инициализации контроллера"""
        controller = ServiceController()
        assert controller.discovery is None
        assert controller.service_port is None

    @patch('main.socket.gethostname')
    @patch('main.socket.gethostbyname_ex')
    def test_get_local_ip_success(self, mock_gethostbyname_ex, mock_gethostname):
        """Тест успешного получения локального IP"""
        mock_gethostname.return_value = 'test-host'
        mock_gethostbyname_ex.return_value = ('test-host', [], ['192.168.1.100', '127.0.0.1'])
        
        ip = ServiceController.get_local_ip()
        assert ip == '192.168.1.100'

    @patch('main.socket.gethostname')
    @patch('main.socket.gethostbyname_ex')
    def test_get_local_ip_fallback(self, mock_gethostbyname_ex, mock_gethostname):
        """Тест получения IP без 192.168.* адреса"""
        mock_gethostname.return_value = 'test-host'
        mock_gethostbyname_ex.return_value = ('test-host', [], ['10.0.0.1', '127.0.0.1'])
        
        ip = ServiceController.get_local_ip()
        assert ip == '10.0.0.1'

    @patch('main.socket.gethostname')
    @patch('main.socket.gethostbyname_ex')
    def test_get_local_ip_exception(self, mock_gethostbyname_ex, mock_gethostname):
        """Тест обработки исключения при получении IP"""
        mock_gethostname.side_effect = Exception("Network error")
        
        ip = ServiceController.get_local_ip()
        assert ip is None

    def test_get_free_port(self):
        """Тест получения свободного порта"""
        port = ServiceController.get_free_port()
        assert isinstance(port, int)
        assert 1024 <= port <= 65535

    def test_cleanup(self):
        """Тест очистки ресурсов"""
        controller = ServiceController()
        controller.discovery = MagicMock()
        
        controller.cleanup()
        # Проверяем, что cleanup не вызывает исключений
        assert True


if __name__ == '__main__':
    pytest.main([__file__])
