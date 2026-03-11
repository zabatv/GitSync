from flask import Flask, request
from flask_socketio import SocketIO 
import subprocess 
import os 
from pathlib import Path

BASE_DIR = Path(__file__).parent

app = Flask(__name__) 
socketio = SocketIO(app, cors_allowed_origins="*") 

@app.route('/') 
def index(): 
    return "Сервер запущен" 

def notify_clients(): 
    socketio.emit('file_updated', {'data': 'Файлы обновлены'}) 

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
        else:
            print(f"Git pull error: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Git pull timeout")
        return False
    except Exception as e:
        print(f"Git pull exception: {e}")
        return False

@socketio.on('connect')
def handle_connect():
    print(f"Клиент подключен: {request.sid}")

@socketio.on('file_updated')
def handle_file_updated(data):
    print(f"Получено уведомление: {data}")
    git_pull()

if __name__ == '__main__': 
    socketio.run(app, port=5000, debug=True)
