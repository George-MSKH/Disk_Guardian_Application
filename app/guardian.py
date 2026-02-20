import psutil
import time
import os
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

CHECK_INTERVAL = 10
ALERT_COOLDOWN = 300

WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

if not WEBHOOK_URL:
    print("WARNING: SLACK_WEBHOOK_URL not set. Alerts are disabled.")


LOG_FILE = "logs/system.log"

# ==============================
# Alert Function
# ==============================

def send_alert(message):
    if not WEBHOOK_URL:
        return

    payload = {"text": f"System Resource Monitor Alert: {message}"}

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)

        if response.status_code != 200:
            print(f"Webhook error: {response.status_code} - {response.text}")
        else:
            print("Alert sent successfully.")

    except Exception as e:
        print(f"Failed to send alert: {e}")

# ==============================
# Logging Function (Readable)
# ==============================

def log_resource(resource, usage_percent, free_gb=None):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    if free_gb is not None:
        line = f"{timestamp} | {resource.upper()} {usage_percent}% ({free_gb}GB free)\n"
    else:
        line = f"{timestamp} | {resource.upper()} {usage_percent}%\n"

    with open(LOG_FILE, "a") as f:
        f.write(line)

def log_separator():
    with open(LOG_FILE, "a") as f:
        f.write("-" * 40 + "\n")


# ==============================
# Resource Checks
# ==============================

def check_disk():
    stats = psutil.disk_usage(CHECK_PATH)
    return stats.percent, stats.free // (2**30)

def check_cpu():
    return psutil.cpu_percent(interval=1)

def check_memory():
    mem = psutil.virtual_memory()
    return mem.percent, mem.available // (2**30)

# ==============================
# Monitoring Logic
# ==============================

def monitor_resources():

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

        # ---- DISK ----
        disk_percent, disk_free = check_disk()
        print(f"[Disk] {disk_percent}% | Free {disk_free}GB")
        log_resource("disk", disk_percent, disk_free)

        if disk_percent > THRESHOLD["disk"]:
            if not alert_active["disk"] or (now - last_alert_time["disk"] > ALERT_COOLDOWN):
                msg = f"Disk usage HIGH: {disk_percent}%"
                send_alert(msg)
                last_alert_time["disk"] = now
                alert_active["disk"] = True
        else:
            alert_active["disk"] = False

        # ---- CPU ----
        cpu_percent = check_cpu()
        print(f"[CPU] {cpu_percent}%")
        log_resource("cpu", cpu_percent)

        if cpu_percent > THRESHOLD["cpu"]:
            if not alert_active["cpu"] or (now - last_alert_time["cpu"] > ALERT_COOLDOWN):
                msg = f"CPU usage HIGH: {cpu_percent}%"
                send_alert(msg)
                last_alert_time["cpu"] = now
                alert_active["cpu"] = True
        else:
            alert_active["cpu"] = False

        # ---- MEMORY ----
        mem_percent, mem_free = check_memory()
        print(f"[Memory] {mem_percent}% | Free {mem_free}GB")
        log_resource("memory", mem_percent, mem_free)

        if mem_percent > THRESHOLD["memory"]:
            if not alert_active["memory"] or (now - last_alert_time["memory"] > ALERT_COOLDOWN):
                msg = f"Memory usage HIGH: {mem_percent}%"
                send_alert(msg)
                last_alert_time["memory"] = now
                alert_active["memory"] = True
        else:
            alert_active["memory"] = False


        log_separator()


        time.sleep(CHECK_INTERVAL)

# ==============================
# Entry
# ==============================

if __name__ == "__main__":
    monitor_resources()

