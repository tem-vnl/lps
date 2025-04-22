import os
import pwd
import time
import psutil

class ProcessMonitor:
    def __init__(self, queue):
        self.queue = queue
        self.username = pwd.getpwuid(os.getuid())[0]
        
    def run(self):
        print("Process monitoring started\n")
        previous_processes = self._get_user_processes()
        
        while True:
            time.sleep(5)
            current_processes = self._get_user_processes()
            started, stopped = self._compare_processes(previous_processes, current_processes)
            
            if started or stopped:
                self.queue.put({"started": started, "stopped": stopped})
                
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