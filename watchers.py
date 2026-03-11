from watchdog.observers import Observer 
from watchdog.events import FileSystemEventHandler 
import subprocess 
import time 
import socketio
from pathlib import Path

BASE_DIR = Path(__file__).parent

class Watcher(FileSystemEventHandler): 
    def __init__(self): 
        super().__init__()
        self.sio = socketio.Client()
        self._connect_to_server()
    
    def _connect_to_server(self):
        max_retries = 10
        for attempt in range(max_retries):
            try:
                self.sio.connect('http://localhost:5000')
                print("Подключено к серверу")
                break
            except Exception as e:
                print(f"Попытка {attempt + 1}/{max_retries}: Сервер недоступен, ожидание...")
                time.sleep(2)
        else:
            print("Не удалось подключиться к серверу")

    def _is_git_file(self, path):
        return '.git' in path or path.endswith('.pyc') or path.endswith('__pycache__')

    def _get_relative_path(self, absolute_path):
        try:
            return str(Path(absolute_path).relative_to(BASE_DIR))
        except ValueError:
            return None

    def _git_commit_push(self, file_path):
        relative_path = self._get_relative_path(file_path)
        if not relative_path:
            return False
        
        try:
            subprocess.run(['git', 'add', relative_path], cwd=str(BASE_DIR), capture_output=True, timeout=10)
            result = subprocess.run(
                ['git', 'commit', '-m', f'Auto: Изменен файл {relative_path}'], 
                cwd=str(BASE_DIR), 
                capture_output=True, 
                text=True,
                timeout=10
            )
            if result.returncode != 0 and 'nothing to commit' not in result.stdout:
                print(f"Git commit error: {result.stderr}")
                return False
            
            if 'nothing to commit' in result.stdout:
                print("Нечего коммитить")
                return True
                
            result = subprocess.run(['git', 'push'], cwd=str(BASE_DIR), capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"Успешно: {relative_path}")
                self.sio.emit('file_updated', {'data': 'Файлы обновлены'})
                return True
            else:
                print(f"Git push error: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("Git timeout")
            return False
        except Exception as e:
            print(f"Git exception: {e}")
            return False

    def on_modified(self, event): 
        if event.is_directory or self._is_git_file(event.src_path):
            return
        print(f'Изменение найдено: {event.src_path}')
        self._git_commit_push(event.src_path)

    def on_created(self, event): 
        if event.is_directory or self._is_git_file(event.src_path):
            return
        print(f'Создан файл: {event.src_path}')
        self._git_commit_push(event.src_path)

    def on_deleted(self, event): 
        if event.is_directory or self._is_git_file(event.src_path):
            return
        print(f'Удален файл: {event.src_path}')
        relative_path = self._get_relative_path(event.src_path)
        if relative_path:
            try:
                subprocess.run(['git', 'add', '-A'], cwd=str(BASE_DIR), capture_output=True, timeout=10)
                subprocess.run(
                    ['git', 'commit', '-m', f'Auto: Удален файл {relative_path}'], 
                    cwd=str(BASE_DIR), 
                    capture_output=True, 
                    timeout=10
                )
                subprocess.run(['git', 'push'], cwd=str(BASE_DIR), capture_output=True, timeout=30)
                self.sio.emit('file_updated', {'data': 'Файлы обновлены'})
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__": 
    path = "."
    event_handler = Watcher() 
    observer = Observer() 
    observer.schedule(event_handler, path, recursive=True) 
    observer.start() 
    print(f"Слежение за: {path}")

    try: 
        while True: 
            time.sleep(1) 
    except KeyboardInterrupt: 
        observer.stop() 
    observer.join()
