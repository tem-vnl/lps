"""
    Browser control module for LPS
    
    Implements a controlled and monitored browser environment for exam sessions.
    Uses Selenium with Chrome to provide a locked-down browsing experience with
    proxy-based content filtering.
"""
import os
import subprocess
import time
import signal
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class Browser:
    """
    A class to manage a controlled browser environment for exam sessions.
    
    Provides a secure browser instance with content filtering via mitmproxy,
    configured to restrict access to approved websites only. Handles launching,
    monitoring, and clean termination of the browser process.

    Attributes:
        driver (webdriver.Chrome): Selenium WebDriver instance for controlling Chrome.
        mitmdump_proc (subprocess.Popen): Process handle for the mitmproxy instance.
        queue (Queue): Queue for receiving commands from the main process.
        browser_process (psutil.Process): Process handle for the browser process.
        pid_queue (Queue): Queue for sending internal PIDs to the main process.
        _active (bool): Flag indicating whether the browser should continue running.
    """
    
    def __init__(self, queue=None, pid_queue=None):
        """
        Initializes the Browser controller.
        
        Sets up communication queues and initializes state variables for
        browser and proxy management.
        
        Args:
            queue (Queue): Queue for receiving commands from the main process.
            pid_queue (Queue): Queue for sending process IDs to be excluded from monitoring.
        """
        self.driver = None
        self.mitmdump_proc = None
        self.queue = queue
        self.browser_process = None
        self.pid_queue = pid_queue
        self._active = True
        
    def run(self):
        """
        Main method to set up and run the controlled browser environment.
        
        Coordinates the setup of the proxy server and browser, handles any exceptions,
        and ensures proper cleanup when the browser session ends.
        """
        try:
            self._setup_mitmdump()
            self._setup_browser()
            self._start_browser()
        except Exception as e:
            print(f"Browser error: {str(e)}")
        finally:
            self._cleanup()
            
    def _setup_mitmdump(self):
        """
        Sets up the mitmproxy server with content filtering.
        
        Launches mitmproxy with a custom script that implements website whitelisting
        to restrict access to approved sites only.
        """
        script_path = os.path.join(os.path.dirname(__file__), "whitelist_mitm.py")
        self.mitmdump_proc = subprocess.Popen(
            ["mitmdump", "-s", script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )
        # Report the process ID to exclude it from monitoring
        self.pid_queue.put(self.mitmdump_proc.pid)
        
    def _setup_browser(self):
        """
        Configures and launches the Chrome browser with security settings.
        
        Sets up Chrome with proxy settings, kiosk mode, and other security
        options to create a locked-down browsing environment for exams.
        """
        proxy = "127.0.0.1:8080"
        print(f"Setting up proxy: {proxy}")

        # Configure Chrome options for secure exam environment
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
        
        # Track browser process and child processes
        self.browser_process = psutil.Process(self.driver.service.process.pid)
        self.pid_queue.put(self.browser_process.pid)
        for p in self.browser_process.children(recursive=True):
            self.pid_queue.put(p.pid)

        
    def _start_browser(self):
        """
        Starts the browser session and monitors for control commands.
        
        Navigates to the initial page and enters a monitoring loop to check
        for commands from the main process, particularly the stop signal.
        """
        print("Testing connection...")
        self.driver.get("https://canvas.kth.se")
        print("Navigation successful")
        
        # Main loop to monitor for stop commands
        while self._active:
            if self.queue:
                try:
                    msg = self.queue.get_nowait()
                    if msg == "STOP":
                        print("Received stop signal, closing browser...")
                        self._active = False
                        break
                except:
                    pass
            time.sleep(0.1)
            
    def _cleanup(self):
        """
        Performs cleanup after the browser session ends.
        
        Ensures proper termination of the browser and proxy processes
        to prevent orphaned processes and resource leaks.
        """
        if self.mitmdump_proc:
            try:
                # Terminate the entire process group to catch child processes
                os.killpg(os.getpgid(self.mitmdump_proc.pid), signal.SIGTERM)
                self.mitmdump_proc.wait(timeout=5)
            except Exception as e:
                print(f"Warning during mitmdump cleanup: {e}")

        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Warning during browser cleanup: {e}")