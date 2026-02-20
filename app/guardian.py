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
THRESHOLD = float(os.getenv("DISK_THRESHOLD", "80.0"))
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
# Monitoring Logic
# ==============================

def monitor_disk():
    print(f"--- Monitoring {CHECK_PATH} (Threshold: {THRESHOLD}%) ---")

    last_alert_time = 0
    alert_active = False  # Tracks whether we're currently in alert state

    while True:
        try:
            stats = psutil.disk_usage(CHECK_PATH)
        except Exception as e:
            print(f"Disk check failed: {e}")
            time.sleep(CHECK_INTERVAL)
            continue

        current_percent = stats.percent
        free_gb = stats.free // (2**30)

        print(f"[Heartbeat] Usage: {current_percent}% | Free: {free_gb}GB")

        now = time.time()

        # ==============================
        # Alert Trigger
        # ==============================
        if current_percent > THRESHOLD:
            if not alert_active or (now - last_alert_time > ALERT_COOLDOWN):
                msg = f"Disk usage HIGH on {CHECK_PATH}: {current_percent}%"
                print(f"!!! {msg}")
                send_alert(msg)
                last_alert_time = now
                alert_active = True

        # ==============================
        # Recovery Detection
        # ==============================
        else:
            if alert_active:
                msg = f"Disk usage RECOVERED on {CHECK_PATH}: {current_percent}%"
                print(f"*** {msg}")
                send_alert(msg)
                alert_active = False

        time.sleep(CHECK_INTERVAL)


# ==============================
# Entry Point
# ==============================

if __name__ == "__main__":
    monitor_disk()
