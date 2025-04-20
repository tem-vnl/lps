import os
import subprocess
import time
import signal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

def start_browser():
    """Wrapper function to start the kiosk browser"""
    driver = None
    mitmdump_proc = None
    
    try:
        script_path = os.path.join(os.path.dirname(__file__), "whitelist_mitm.py")
        mitmdump_proc = subprocess.Popen(
            ["mitmdump", "-s", script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid  # so we can kill the process group later
        )

        try:
            proxy = "127.0.0.1:8080"
            print(f"Setting up proxy: {proxy}")

            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--proxy-server=http://{proxy}")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--start-maximized")
            options.add_argument("--kiosk")  # Force fullscreen
            options.add_argument("--verbose")
            options.add_argument("--log-level=0")

            print("Installing ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            
            print("Launching Chrome...")
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)
            print("Chrome launched successfully")

            print("Testing connection...")
            driver.get("https://canvas.kth.se")
            print("Navigation successful")
            
            # Keep browser running until parent process exits
            while True:
                time.sleep(1)

        except WebDriverException as e:
            print(f"WebDriver error: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise

    except (FileNotFoundError, KeyboardInterrupt, EOFError):
        print("\nBrowser shutting down...")
    finally:
        if mitmdump_proc:
            try:
                os.killpg(os.getpgid(mitmdump_proc.pid), signal.SIGTERM)
                mitmdump_proc.wait(timeout=5)
            except Exception as e:
                print(f"Warning during mitmdump cleanup: {e}")

        if driver:
            try:
                driver.quit()
            except Exception as e:
                print(f"Warning during browser cleanup: {e}")

def main():
    start_browser()

if __name__ == "__main__":
    main()