import pytest
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGUI:
    """Тесты для GUI компонентов"""

    def test_gui_import(self):
        """Тест импорта GUI модуля"""
        try:
            from gui import LANChatGUI, main
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import GUI module: {e}")

    def test_gui_main_function(self):
        """Тест функции main в GUI"""
        try:
            from gui import main
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import GUI main function: {e}")

    def test_gui_class_exists(self):
        """Тест существования класса GUI"""
        try:
            from gui import LANChatGUI
            assert LANChatGUI is not None
        except ImportError as e:
            pytest.fail(f"Failed to import GUI class: {e}")


class TestGUIFeatures:
    """Тесты для функций GUI"""

    def test_gui_has_chat_methods(self):
        """Тест наличия методов чата в классе GUI"""
        try:
            from gui import LANChatGUI
            
            # Проверяем, что класс имеет необходимые методы
            assert hasattr(LANChatGUI, 'send_message')
            assert hasattr(LANChatGUI, 'add_message')
            assert hasattr(LANChatGUI, 'toggle_chat')
            
        except ImportError as e:
            pytest.fail(f"Failed to import GUI class: {e}")

    def test_gui_has_file_methods(self):
        """Тест наличия методов файлов в классе GUI"""
        try:
            from gui import LANChatGUI
            
            # Проверяем, что класс имеет необходимые методы
            assert hasattr(LANChatGUI, 'browse_file_for_chat')
            assert hasattr(LANChatGUI, 'add_file_message')
            assert hasattr(LANChatGUI, 'download_file_from_chat')
            
        except ImportError as e:
            pytest.fail(f"Failed to import GUI class: {e}")

    def test_gui_has_device_methods(self):
        """Тест наличия методов обнаружения устройств в классе GUI"""
        try:
            from gui import LANChatGUI
            
            # Проверяем, что класс имеет необходимые методы
            assert hasattr(LANChatGUI, 'refresh_devices')
            assert hasattr(LANChatGUI, 'connect_to_device')
            
        except ImportError as e:
            pytest.fail(f"Failed to import GUI class: {e}")


if __name__ == '__main__':
    pytest.main([__file__])
