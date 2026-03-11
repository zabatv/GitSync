import subprocess 
from pathlib import Path
import time
import socket
import socketio

BASE_DIR = Path(__file__).parent

sio = socketio.Client()

def wait_for_server(host='localhost', port=5000, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(1)
    return False

def git_pull():
    try:
        result = subprocess.run(
            ['git', 'pull'], 
            cwd=str(BASE_DIR), 
            capture_output=True, 
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"Git pull success: {result.stdout}")
            return True
        else:
            print(f"Git pull error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("Git pull timeout")
        return False
    except Exception as e:
        print(f"Git pull exception: {e}")
        return False

@sio.on('file_updated') 
def handle_file_updated(data): 
    print(f'Обновление получено: {data["data"]}') 
    git_pull()

@sio.on('connect')
def handle_connect():
    print('Подключено к серверу')

@sio.on('disconnect')
def handle_disconnect():
    print('Отключено от сервера')

if __name__ == '__main__': 
    print("Ожидание сервера...")
    if wait_for_server():
        print("Сервер доступен, подключение...")
        try:
            sio.connect('http://localhost:5000')
            sio.wait()
        except Exception as e:
            print(f"Ошибка подключения: {e}")
    else:
        print("Сервер недоступен")
