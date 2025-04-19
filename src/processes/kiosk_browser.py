import os
import subprocess
import tempfile
import time
import signal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from contextlib import contextmanager
import shutil

@contextmanager
def temporary_script():
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, "whitelist_mitm.py")
    
    # Try multiple possible locations for the whitelist script
    possible_locations = [
        os.path.join(os.path.dirname(__file__), "whitelist_mitm.py"),  # in processes folder
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "whitelist_mitm.py"),  # in src folder
    ]
    
    for original_script in possible_locations:
        if os.path.exists(original_script):
            try:
                shutil.copy2(original_script, script_path)
                yield script_path
                return
            finally:
                try:
                    os.remove(script_path)
                except OSError:
                    pass
    
    raise FileNotFoundError("Could not find whitelist_mitm.py in any expected location")

# === Step 2: Start mitmdump with the whitelist script ===
try:
    with temporary_script() as script_path:
        mitmdump_proc = subprocess.Popen(
            ["mitmdump", "-s", script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid  # so we can kill the process group later
        )

        # Wait and check if process is still running
        time.sleep(3)
        if mitmdump_proc.poll() is not None:
            print("Error: mitmdump failed to start")
            exit(1)

        try:
            # === Step 3: Set up Selenium to use the proxy ===
            proxy = "127.0.0.1:8080"
            print(f"Setting up proxy: {proxy}")

            options = Options()
            # Temporarily disable headless for debugging
            # options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--proxy-server=http://{proxy}")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--start-maximized")  # Start maximized
            options.add_argument("--kiosk")  # Force fullscreen
            options.add_argument("--verbose")
            options.add_argument("--log-level=0")

            try:
                print("Installing ChromeDriver...")
                service = Service(ChromeDriverManager().install())
                
                print("Launching Chrome...")
                driver = webdriver.Chrome(service=service, options=options)
                driver.set_page_load_timeout(30)
                print("Chrome launched successfully")

                print("Testing connection...")
                driver.get("https://www.google.com")
                print("Navigation successful")
                input("Press Enter to exit...")

            except webdriver.exceptions.WebDriverException as e:
                print(f"WebDriver error: {str(e)}")
                raise
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                raise

        finally:
            # === Step 5: Cleanup ===
            print("Cleaning up...")
            try:
                os.killpg(os.getpgid(mitmdump_proc.pid), signal.SIGTERM)  # kill mitmdump process group
                mitmdump_proc.wait(timeout=5)  # Wait up to 5 seconds for clean shutdown
            except (ProcessLookupError, subprocess.TimeoutExpired) as e:
                print(f"Warning during cleanup: {e}")

            # Close browser
            try:
                driver.quit()
            except Exception as e:
                print(f"Warning: Could not close browser cleanly: {e}")

except FileNotFoundError:
    print("Error: mitmdump not found. Please install mitmproxy.")
    exit(1)
