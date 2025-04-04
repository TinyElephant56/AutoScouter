#generated with chatgpt, the gpu checking doesnt work for mac and searching online, idk if anyone else has done it.
import psutil
import time
import shutil
import subprocess

import re

def get_mac_gpu_usage():
    try:
        output = subprocess.check_output(["ioreg", "-r", "-d", "1", "-c", "AGXAccelerator"], stderr=subprocess.DEVNULL)
        output = output.decode("utf-8", errors="ignore")

        # Extract GPU utilization (search for 'busy%')
        with open('deleteme.txt', 'w') as file:
            file.write(output)
        match = re.search(r'"busy"=(\d+)', output)
        if match:
            return f"GPU Usage: {match.group(1)}%"
        else:
            return "GPU Usage: Not found"
    except Exception as e:
        return f"Error fetching GPU usage: {e}"


def get_cpu_usage():
    return f"CPU Usage: {psutil.cpu_percent()}%"

def get_storage_info():
    total, used, free = shutil.disk_usage("/")
    return f"Storage: {free / (1024 ** 3):.2f} GB free / {total / (1024 ** 3):.2f} GB total"

def get_network_usage():
    net_io = psutil.net_io_counters()
    return f"Network: {net_io.bytes_sent / (1024 ** 2):.2f} MB sent, {net_io.bytes_recv / (1024 ** 2):.2f} MB received"

if __name__ == "__main__":
    while True:
        print(get_mac_gpu_usage())
        print(get_cpu_usage())
        print(get_storage_info())
        print(get_network_usage())
        print("-" * 40)
        time.sleep(100)
