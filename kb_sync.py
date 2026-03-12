import os
import sys
import time
import paramiko
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import threading
import hashlib

SERVER = '192.168.0.104'
USER = 'tali'
PASSWORD = '3278'
REMOTE_FOLDER = '/home/tali/kb'

local_folder = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

default_path = os.path.join(os.path.expanduser('~'), 'Obsidian', 'БазаЗнаний')
if not os.path.exists(default_path):
    os.makedirs(default_path, exist_ok=True)

local_folder = default_path

def get_file_hash(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

class SyncHandler(FileSystemEventHandler):
    def __init__(self, sftp, remote_base):
        self.sftp = sftp
        self.remote_base = remote_base
        self.processing = set()
        
    def _get_remote_path(self, local_path):
        rel = Path(local_path).relative_to(Path(local_folder))
        return f"{self.remote_base}/{rel}".replace("\\", "/")
    
    def _get_local_path(self, remote_path):
        rel = remote_path.replace(self.remote_base + '/', '')
        return os.path.join(local_folder, rel.replace('/', '\\'))
    
    def _mkdir_p(self, remote_path):
        dirs = remote_path.split('/')
        path = ''
        for d in dirs:
            path = path + d + '/' if path else d + '/'
            try:
                self.sftp.stat(path)
            except:
                try:
                    self.sftp.mkdir(path)
                except:
                    pass

    def upload_file(self, path):
        try:
            remote_path = self._get_remote_path(path)
            parent = str(Path(remote_path).parent)
            self._mkdir_p(parent)
            self.sftp.put(path, remote_path)
            print(f"UP: {Path(path).name}")
        except Exception as e:
            print(f"Upload error: {e}")

    def on_created(self, event):
        if event.is_directory: return
        path = Path(event.src_path)
        if path.suffix in ['.pyc', '.tmp'] or '.git' in str(path): return
        time.sleep(0.3)
        if str(path) not in self.processing:
            self.processing.add(str(path))
            self.upload_file(path)
            self.processing.discard(str(path))

    def on_modified(self, event):
        if event.is_directory: return
        path = Path(event.src_path)
        if path.suffix in ['.pyc', '.tmp'] or '.git' in str(path): return
        time.sleep(0.3)
        if str(path) not in self.processing:
            self.processing.add(str(path))
            self.upload_file(path)
            self.processing.discard(str(path))

def download_changes(sftp, handler):
    def get_remote_files(path, files):
        try:
            items = sftp.listdir(path)
        except:
            return files
        for item in items:
            remote_file = f"{path}/{item}"
            try:
                stat = sftp.stat(remote_file)
                if stat.st_mode & 0o40000:
                    get_remote_files(remote_file, files)
                else:
                    files.append(remote_file)
            except:
                pass
        return files

    while True:
        try:
            remote_files = get_remote_files(REMOTE_FOLDER, [])
            local_folder_path = Path(local_folder)
            
            for remote_file in remote_files:
                local_file = handler._get_local_path(remote_file)
                os.makedirs(os.path.dirname(local_file), exist_ok=True)
                
                try:
                    local_hash = get_file_hash(local_file)
                except:
                    local_hash = None
                
                try:
                    with sftp.open(remote_file, 'rb') as rf:
                        remote_content = rf.read()
                        remote_hash = hashlib.md5(remote_content).hexdigest()
                except:
                    continue
                
                if local_hash != remote_hash:
                    with open(local_file, 'wb') as lf:
                        lf.write(remote_content)
                    print(f"DOWN: {Path(local_file).name}")
                    
        except Exception as e:
            print(f"Sync error: {e}")
        
        time.sleep(5)

def connect_and_sync():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD)
    sftp = ssh.open_sftp()
    
    def download_dir(remote_path, local_path):
        try:
            items = sftp.listdir(remote_path)
        except:
            items = []
            try:
                sftp.mkdir(remote_path)
            except: pass
            
        for item in items:
            remote_file = f"{remote_path}/{item}"
            local_file = os.path.join(local_path, item)
            try:
                stat = sftp.stat(remote_file)
                if stat.st_mode & 0o40000:
                    os.makedirs(local_file, exist_ok=True)
                    download_dir(remote_file, local_file)
                else:
                    if not os.path.exists(local_file):
                        os.makedirs(local_path, exist_ok=True)
                        sftp.get(remote_file, local_file)
                        print(f"INIT: {item}")
            except Exception as e:
                print(f"Error {remote_file}: {e}")
    
    print("Initial sync...")
    download_dir(REMOTE_FOLDER, local_folder)
    
    handler = SyncHandler(sftp, REMOTE_FOLDER)
    observer = Observer()
    observer.schedule(handler, local_folder, recursive=True)
    observer.start()
    
    sync_thread = threading.Thread(target=download_changes, args=(sftp, handler), daemon=True)
    sync_thread.start()
    
    print(f"Watching: {local_folder}")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    sftp.close()
    ssh.close()

if __name__ == "__main__":
    connect_and_sync()
