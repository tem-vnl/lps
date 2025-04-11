import subprocess
import pwd
import sys
import os
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

# Constants
BROWSER_USER = "browseruser"
DEFAULT_URL = "https://example.com"
CHROME_DATA_DIR = "chrome-data"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrowserSetupError(Exception):
    """Custom exception for browser setup failures"""
    pass

def run_cmd(cmd, check=True):
    """Run system command and return result"""
    try:
        logger.debug(f"Running command: {' '.join(cmd)}")
        return subprocess.run(cmd, check=check, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        raise

def get_uid(username):
    """Get user ID for given username"""
    try:
        return pwd.getpwnam(username).pw_uid
    except KeyError:
        raise BrowserSetupError(f"User '{username}' does not exist")

def set_default_deny():
    """Set default firewall policy to DROP"""
    logger.info("Setting default policy to DROP")
    try:
        run_cmd(["sudo", "iptables", "-P", "OUTPUT", "DROP"])
        # Allow DNS and localhost
        run_cmd(["sudo", "iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "ACCEPT"])
        run_cmd(["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"])
    except subprocess.CalledProcessError:
        raise BrowserSetupError("Failed to set firewall rules")

def allow_user(username):
    """Allow network access for specific user"""
    uid = get_uid(username)
    logger.info(f"Allowing network access for UID {uid} ({username})")
    run_cmd(["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", str(uid), "-j", "ACCEPT"])

def remove_allow_rule(username):
    """Remove network access rule for user"""
    uid = get_uid(username)
    result = run_cmd(["sudo", "iptables", "-L", "OUTPUT", "--line-numbers", "-n"])
    lines = result.stdout.strip().splitlines()
    for line in reversed(lines):
        if f"owner UID match {uid}" in line:
            line_num = line.split()[0]
            logger.info(f"Removing ACCEPT rule for UID {uid} at line {line_num}")
            run_cmd(["sudo", "iptables", "-D", "OUTPUT", line_num])
            break

def reset_firewall():
    """Reset firewall to default ACCEPT policy"""
    logger.info("Resetting OUTPUT policy to ACCEPT")
    run_cmd(["sudo", "iptables", "-P", "OUTPUT", "ACCEPT"])

def setup_chrome_environment(username):
    """Setup Chrome environment for user"""
    user_home = Path(f"/home/{username}")
    chrome_dir = user_home / CHROME_DATA_DIR
    
    if not chrome_dir.exists():
        chrome_dir.mkdir(parents=True, exist_ok=True)
        run_cmd(["sudo", "chown", "-R", f"{username}:{username}", str(chrome_dir)])
    
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-data-dir={chrome_dir}")
    options.add_argument("--start-maximized")
    return options

def run_browser_as_user(username):
    """Run browser as specified user"""
    user_info = pwd.getpwnam(username)
    uid = user_info.pw_uid
    gid = user_info.pw_gid

    chrome_options = setup_chrome_environment(username)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Drop privileges after browser initialization
        os.setgid(gid)
        os.setuid(uid)
        
        driver.get(DEFAULT_URL)
        logger.info("Browser is open. Close the window to finish.")
        
        while True:
            try:
                _ = driver.window_handles
                time.sleep(1)
            except WebDriverException:
                break
            
    except Exception as e:
        logger.error(f"Browser error: {e}")
        raise
    finally:
        if 'driver' in locals():
            driver.quit()
        logger.info("Browser closed")

def ensure_browser_user():
    """Ensure browser user exists"""
    try:
        get_uid(BROWSER_USER)
    except BrowserSetupError:
        logger.info(f"Creating user {BROWSER_USER}")
        run_cmd(["sudo", "useradd", "-m", BROWSER_USER])

def ensure_dependencies():
    """Ensure all required packages are installed"""
    try:
        # Get the current Python executable path
        python_path = sys.executable
        logger.info(f"Installing dependencies using {python_path}")
        run_cmd([
            "sudo", 
            python_path, 
            "-m", 
            "pip", 
            "install", 
            "selenium", 
            "webdriver-manager"
        ])
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        raise BrowserSetupError("Dependencies installation failed")

def main():
    """Main function"""
    if os.geteuid() != 0:
        logger.error("This script requires root privileges")
        sys.exit(1)

    try:
        ensure_dependencies()
        ensure_browser_user()
        set_default_deny()
        allow_user(BROWSER_USER)
        run_browser_as_user(BROWSER_USER)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        remove_allow_rule(BROWSER_USER)
        reset_firewall()

if __name__ == "__main__":
    main()
