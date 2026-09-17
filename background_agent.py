import time
import threading
import psutil
from voice import speak

# List to hold pending reminders: [{'time': timestamp, 'message': text}]
reminders = []
reminders_lock = threading.Lock()

# Flags to prevent Iris from spamming warnings continuously
battery_alert_sent = False
cpu_alert_sent = False

def set_reminder(seconds: int, message: str) -> str:
    """Tool for setting a timed reminder in seconds."""
    target_time = time.time() + seconds
    with reminders_lock:
        reminders.append({"time": target_time, "message": message})
    
    print(f"[BACKGROUND AGENT] Scheduled reminder in {seconds} sec: {message}")
    if seconds >= 60:
        mins = round(seconds / 60, 1)
        return f"Reminder set for {mins} minute(s) from now: '{message}'."
    return f"Reminder set for {seconds} seconds from now: '{message}'."

def monitor_system():
    """Checks hardware health metrics."""
    global battery_alert_sent, cpu_alert_sent
    
    # 1. Battery Health Check
    battery = psutil.sensors_battery()
    if battery and not battery.power_plugged:
        if battery.percent <= 20 and not battery_alert_sent:
            speak(f"Warning: Your battery level is low at {battery.percent}%. Please plug in your charger.")
            battery_alert_sent = True
        elif battery.percent > 25:
            battery_alert_sent = False  # Reset flag when charged back up
            
    # 2. CPU Usage Spike Check
    cpu_usage = psutil.cpu_percent(interval=None)
    if cpu_usage >= 90 and not cpu_alert_sent:
        speak("Alert: System CPU load is currently over 90%. Performance may slow down.")
        cpu_alert_sent = True
    elif cpu_usage < 70:
        cpu_alert_sent = False  # Reset flag when CPU cools down

def check_reminders():
    """Checks if any scheduled reminders are due."""
    now = time.time()
    with reminders_lock:
        for reminder in reminders[:]:
            if now >= reminder["time"]:
                print(f"[BACKGROUND AGENT] Triggering reminder: {reminder['message']}")
                speak(f"Attention! You asked me to remind you: {reminder['message']}")
                reminders.remove(reminder)

def background_loop():
    """Continuous polling loop running in the background thread."""
    print("[BACKGROUND AGENT] Proactive monitoring thread active.")
    while True:
        try:
            monitor_system()
            check_reminders()
        except Exception as e:
            print(f"[BACKGROUND AGENT ERROR] {e}")
            
        # Poll every 10 seconds to keep CPU usage virtually 0%
        time.sleep(10)

def start_background_agent():
    """Launches the background agent thread on app startup."""
    agent_thread = threading.Thread(target=background_loop, daemon=True)
    agent_thread.start()