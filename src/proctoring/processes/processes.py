import psutil
import os
from datetime import datetime
import time

class ProcessMonitor:
    def __init__(self, queue):
        self.queue = queue
        self.current_user = os.getlogin()
        self.initial_processes = self._get_current_processes()
        self.previous_processes = set()
        self.start_time = datetime.now()

    def _get_current_processes(self):
        processes = set()
        for process in psutil.process_iter(['pid', 'name', 'username']):
            try:
                if process.info['username'] == self.current_user:
                    processes.add((process.info['pid'], process.info['name']))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def run(self):
        try:
            while True:
                current_processes = self._get_current_processes()
                new_processes = current_processes - self.initial_processes
                
                # Report any new processes with timestamp
                for pid, name in new_processes - self.previous_processes:
                    msg = {
                        'timestamp': datetime.now(),
                        'pid': pid,
                        'name': name,
                        'type': 'new_process'
                    }
                    self.queue.put(msg)
                
                self.previous_processes = new_processes
                time.sleep(1)
        except Exception as e:
            print(f"Process monitoring error: {e}")