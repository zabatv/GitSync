@echo off
REM Создание виртуального окружения
python -m venv venv
call venv\Scripts\activate

REM Установка необходимых библиотек
pip install Flask Flask-SocketIO watchdog

REM Создание server.py
echo from flask import Flask > server.py
echo from flask_socketio import SocketIO >> server.py
echo import subprocess >> server.py
echo import os >> server.py
echo  >> server.py
echo app = Flask(__name__) >> server.py
echo socketio = SocketIO(app) >> server.py
echo  >> server.py
echo @app.route('/') >> server.py
echo def index(): >> server.py
echo     return "Сервер запущен" >> server.py
echo  >> server.py
echo def notify_clients(): >> server.py
echo     socketio.emit('file_updated', {'data': 'Файлы обновлены'}) >> server.py
echo  >> server.py
echo def git_pull(): >> server.py
echo     subprocess.call(['git', 'pull']) >> server.py
echo  >> server.py
echo if __name__ == '__main__': >> server.py
echo     socketio.run(app, port=5000) >> server.py

REM Создание watchers.py
echo from watchdog.observers import Observer > watchers.py
echo from watchdog.events import FileSystemEventHandler >> watchers.py
echo import subprocess >> watchers.py
echo import time >> watchers.py
echo import socketio >> watchers.py
echo  >> watchers.py
echo class Watcher(FileSystemEventHandler): >> watchers.py
echo     def __init__(self): >> watchers.py
echo         self.sio = socketio.Client() >> watchers.py
echo         self.sio.connect('http://localhost:5000') >> watchers.py
echo     >> watchers.py
echo     def on_modified(self, event): >> watchers.py
echo         print(f'Изменение найдено в {event.src_path}') >> watchers.py
echo         subprocess.call(['git', 'add', event.src_path]) >> watchers.py
echo         subprocess.call(['git', 'commit', '-m', f'Изменение в {event.src_path}']) >> watchers.py
echo         subprocess.call(['git', 'push']) >> watchers.py
echo         self.sio.emit('file_updated', {'data': 'Файлы обновлены'}) >> watchers.py
echo  >> watchers.py
echo if __name__ == "__main__": >> watchers.py
echo     path = "./ваша_папка"  # Укажите свою папку >> watchers.py
echo     event_handler = Watcher() >> watchers.py
echo     observer = Observer() >> watchers.py
echo     observer.schedule(event_handler, path, recursive=True) >> watchers.py
echo     observer.start() >> watchers.py
echo  >> watchers.py
echo     try: >> watchers.py
echo         while True: >> watchers.py
echo             time.sleep(1) >> watchers.py
echo     except KeyboardInterrupt: >> watchers.py
echo         observer.stop() >> watchers.py
echo     observer.join() >> watchers.py

REM Создание client.py
echo import subprocess > client.py
echo import json >> client.py
echo from flask import Flask >> client.py
echo from flask_socketio import SocketIO >> client.py
echo  >> client.py
echo app = Flask(__name__) >> client.py
echo socketio = SocketIO(app) >> client.py
echo  >> client.py
echo @socketio.on('file_updated') >> client.py
echo def handle_file_updated(data): >> client.py
echo     print(f'Обновление получено: {data["data"]}') >> client.py
echo     subprocess.call(['git', 'pull']) >> client.py
echo  >> client.py
echo if __name__ == '__main__': >> client.py
echo     socketio.run(app, port=5001) >> client.py

echo Все файлы созданы!
pause
