import psutil
import time

TARGET_APP = "Calculator"  # Use the process name exactly as it appears in 'ps aux'

def is_app_running(app_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and app_name.lower() in proc.info['name'].lower():
            return True
    return False

print(f"Monitoring for {TARGET_APP}...")

while True:
    if is_app_running(TARGET_APP):
        print(f"{TARGET_APP} is running!")
    else :
        break
    time.sleep(5)  # Check every 5 seconds
print("closed")