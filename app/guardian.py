import psutil
import time
import os
import json 
import requests
from dotenv import load_dotenv

load_dotenv()

# ==============================
# Configuration
# ==============================

CHECK_PATH = "/host" if os.path.exists("/host") else "/"
THRESHOLD = {
    "disk": float(os.getenv("DISK_THRESHOLD", "80.0")),
    "cpu": float(os.getenv("CPU_THRESHOLD", "75.0")),
    "memory": float(os.getenv("MEM_THRESHOLD", "80.0"))
}
CHECK_INTERVAL = 10  # seconds
ALERT_COOLDOWN = 300  # seconds (5 minutes)

WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

if not WEBHOOK_URL:
    print("WARNING: SLACK_WEBHOOK_URL not set. Alerts are disabled.")

# ==============================
# Alert Function
# ==============================

def send_alert(message):
    if not WEBHOOK_URL:
        return

    payload = {"text": f"Disk Guardian Alert: {message}"}

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)

        if response.status_code != 200:
            print(f"Webhook error: {response.status_code} - {response.text}")
        else:
            print("Alert sent successfully.")

    except Exception as e:
        print(f"Failed to send alert: {e}")


# ==============================
# Log setup
# ==============================


HEARTBEAT_LOG_FILE = f"logs/heartbeat_log_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json"
ALERT_LOG_FILE = f"logs/alert_log_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json"

# ==============================
# Logging functions
# ==============================

def log_heartbeat(resource, usage_percent, free_gb=None):

    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "resource": resource,
        "usage_percent": usage_percent,
        "free_gb": free_gb
    }

    try:
        with open(HEARTBEAT_LOG_FILE, "r") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    logs.append(entry)
    with open (HEARTBEAT_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def log_alert(resource, usage_percent, free_gb=None, alert_type="HIGH"):
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "resource": resource,
        "usage_percent": usage_percent,
        "free_gb": free_gb,
        "alert": alert_type
    }

    try:
        with open(ALERT_LOG_FILE, "r") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    logs.append(entry)
    with open (ALERT_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

        
# ==============================
# Resource check functions
# ==============================
        
def check_disk():
    stats = psutil.disk_usage(CHECK_PATH)
    percent = stats.percent
    free_gb = stats.free // (2**30)
    return percent, free_gb

def check_cpu():
    percent = psutil.cpu_percent(interval=1)
    return percent

def check_memory():
    mem = psutil.virtual_memory()
    percent = mem.percent
    free_gb = mem.available // (2**30)
    return percent, free_gb

# ==============================
# Monitoring Logic
# ==============================

def monitor_resources():
    print(f"--- Monitoring {CHECK_PATH} (Threshold: {THRESHOLD}%) ---")

    last_alert_time = {
        "disk": 0,
        "cpu": 0,
        "memory": 0
    }

    alert_active = {
        "disk": False,
        "cpu": False,
        "memory": False
    } 

    while True:
        now = time.time()

        #---------------------
        # DISK CHECK
        #---------------------

        disk_percent, disk_free = check_disk()
        print(f"[Disk] Usage: {disk_percent}% | Free: {disk_free}GB")
        log_heartbeat("disk", disk_percent, free_gb=disk_free)

        if disk_percent > THRESHOLD["disk"]:
            if not alert_active["disk"] or (now - last_alert_time["disk"] > ALERT_COOLDOWN):
                msg = f"Disk usage HIGH on {CHECK_PATH}: {disk_percent}%"
                print(f"!!! {msg}")
                send_alert(msg)
                log_alert("disk", disk_percent, free_gb=disk_free, alert_type="HIGH")
                last_alert_time["disk"] = now
                alert_active["disk"] = True
        else: 
            if alert_active["disk"]:
                msg = f"Disk usage RECOVERED on {CHECK_PATH}: {disk_percent}%"
                print(f"*** {msg}")
                send_alert(msg)
                log_alert("disk", disk_percent, free_gb=disk_free, alert_type="RECOVERED")
                alert_active = False

        #---------------------
        # CPU CHECK
        #---------------------

        cpu_percent = check_cpu()
        print(f"[CPU] Usage: {cpu_percent}%")
        log_heartbeat("cpu", cpu_percent)

        if cpu_percent > THRESHOLD["cpu"]:
            if not alert_active["cpu"] or (now - last_alert_time["cpu"] > ALERT_COOLDOWN):
                msg = f"[CPU] Usage HIGH: {cpu_percent}%"
                print(f"!!! {msg}")
                send_alert(msg)
                log_alert("cpu", cpu_percent, alert_type="HIGH")
                last_alert_time["cpu"] = now
                alert_active = True
        else:
            if alert_active["cpu"]:
                msg = f"CPU usage RECOVERED: {cpu_percent}%"
                print(f"*** {msg}")
                send_alert(msg)
                log_alert("cpu", cpu_percent, alert_type="RECOVERED")
                alert_active = False

        #---------------------
        # MEMORY CHECK
        #---------------------

        mem_percent, mem_free = check_memory()
        print(f"[Memory] Usage: {mem_percent}% | Free {mem_free}GB")
        log_heartbeat("memory", mem_percent, free_gb=mem_free)

        if mem_percent > THRESHOLD["memory"]:
            if not alert_active["memory"] or (now - last_alert_time["memory"] > ALERT_COOLDOWN):
                msg = f"Memory usage HIGH: {mem_percent}%"
                print(f"!!! {msg}")
                send_alert(msg)
                log_alert("memory", mem_percent, free_gb=mem_free, alert_type="HIGH")
                last_alert_time["memory"] = now
                alert_active = True
        else:
            if alert_active["memory"]:
                msg = f"Memory usage RECOVERED: {mem_percent}%"
                print(f"*** {msg}")
                send_alert(msg)
                log_alert("memory", mem_percent, free_gb=mem_free, alert_type="RECOVERED")
                alert_active = False
                
        # --------------------
        # Wait for next check
        # --------------------

        time.sleep(CHECK_INTERVAL)


# ==============================
# Entry Point
# ==============================

if __name__ == "__main__":
    monitor_resources()
