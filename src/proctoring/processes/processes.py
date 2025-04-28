import os
import pwd
import time
import psutil
from multiprocessing import Process
from datetime import datetime

class ProcessMonitor:
    def __init__(self, queue, pid_queue):
        self.queue = queue
        self.username = pwd.getpwuid(os.getuid())[0]
        self.safe_processes = open(os.path.join(os.path.dirname(__file__), "whitelist.txt")).read().splitlines()
        self.pid_queue = pid_queue
        self.safe_pid = set()
        
    def run(self):
        print("Process monitoring started\n")
        previous_processes = self._get_user_processes()
        self.known_pids = set()  # Track PIDs we've already reported
        
        while True:
            time.sleep(1)  # Check more frequently
            current_processes = self._get_user_processes()
            started, stopped = self._compare_processes(previous_processes, current_processes)

            while not self.pid_queue.empty():
                self.safe_pid.add(self.pid_queue.get())
            
            if started:
                for name, pidarray in started.items():
                    if len([safe for safe in self.safe_processes if safe in name]) < 1:
                        for pid in pidarray:
                            if pid['pid'] in self.safe_pid or pid['pid'] in self.known_pids:
                                continue
                            self._kill_process(pid['pid'])
                            self.known_pids.add(pid['pid'])
                            self.queue.put({
                                'type': 'new_process',
                                'timestamp': datetime.now(),
                                'pid': pid['pid'],
                                'name': name
                            })
                
            previous_processes = current_processes
            
    def _get_user_processes(self):
        processes_dict = {}
        for process in psutil.process_iter(['pid', 'name', 'username']):
            try:
                if process.info['username'] == self.username:
                    proc_name = process.info['name']
                    proc_info = {
                        "pid": process.info['pid'],
                        "username": process.info['username']
                    }
                    if proc_name not in processes_dict:
                        processes_dict[proc_name] = []
                    processes_dict[proc_name].append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes_dict

    def _compare_processes(self, old, new):
        started = {}
        stopped = {}

        # Detect started
        for name, new_list in new.items():
            old_list = old.get(name, [])
            new_pids = {proc['pid'] for proc in new_list}
            old_pids = {proc['pid'] for proc in old_list}
            added_pids = new_pids - old_pids
            if added_pids:
                started[name] = [proc for proc in new_list if proc['pid'] in added_pids]

        # Detect stopped
        for name, old_list in old.items():
            new_list = new.get(name, [])
            old_pids = {proc['pid'] for proc in old_list}
            new_pids = {proc['pid'] for proc in new_list}
            removed_pids = old_pids - new_pids
            if removed_pids:
                stopped[name] = [proc for proc in old_list if proc['pid'] in removed_pids]

        return started, stopped
    
    def _kill_process(self, pid):
        try:
            process = psutil.Process(pid)
            for subprocess in process.children(recursive=True):
                self._kill_process(subprocess.pid)
            if process.is_running: process.kill()
        except Exception as e:
            print(f"Couldn't gracefully terminate PID: {pid}")