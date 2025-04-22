import os
import subprocess
import time
import signal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class Browser:
    def __init__(self):
        self.driver = None
        self.mitmdump_proc = None
        
    def run(self):
        try:
            self._setup_mitmdump()
            self._setup_browser()
            self._start_browser()
        except Exception as e:
            print(f"Browser error: {str(e)}")
        finally:
            self._cleanup()
            
    def _setup_mitmdump(self):
        script_path = os.path.join(os.path.dirname(__file__), "whitelist_mitm.py")
        self.mitmdump_proc = subprocess.Popen(
            ["mitmdump", "-s", script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )
        
    def _setup_browser(self):
        proxy = "127.0.0.1:8080"
        print(f"Setting up proxy: {proxy}")

        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--proxy-server=http://{proxy}")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--start-maximized")
        options.add_argument("--kiosk")
        options.add_argument("--verbose")
        options.add_argument("--log-level=0")

        print("Installing ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        
        print("Launching Chrome...")
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(30)
        print("Chrome launched successfully")
        
    def _start_browser(self):
        print("Testing connection...")
        self.driver.get("https://canvas.kth.se")
        print("Navigation successful")
        
        while True:
            time.sleep(1)
            
    def _cleanup(self):
        if self.mitmdump_proc:
            try:
                os.killpg(os.getpgid(self.mitmdump_proc.pid), signal.SIGTERM)
                self.mitmdump_proc.wait(timeout=5)
            except Exception as e:
                print(f"Warning during mitmdump cleanup: {e}")

        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Warning during browser cleanup: {e}")

def main():
    browser = Browser()
    browser.run()

if __name__ == "__main__":
    main()