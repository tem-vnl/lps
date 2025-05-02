"""
    Process monitoring module for LPS
"""
import os
import pwd
import time
import psutil
from multiprocessing import Process
from datetime import datetime

class ProcessMonitor:
    """
    A class to monitor and control system processes during exam sessions.
    
    Tracks new processes started by the user during an exam, terminates unauthorized
    processes, and reports violations to the main proctoring system.
    
    Attributes:
        queue (Queue): Queue for sending process events to the main process.
        username (str): Current user's username.
        safe_processes (list): List of whitelisted process names.
        pid_queue (Queue): Queue for receiving internal PIDs to exclude from monitoring.
        safe_pid (set): Set of process IDs that are part of the proctoring system.
        known_pids (set): Set of process IDs already reported.
    """
    
    def __init__(self, queue, pid_queue):
        """
        Initializes the ProcessMonitor with communication queues and loads whitelist.
        
        Args:
            queue (Queue): Queue for sending process events to the main process.
            pid_queue (Queue): Queue for receiving internal PIDs to exclude from monitoring.
        """
        self.queue = queue
        self.username = pwd.getpwuid(os.getuid())[0]
        self.safe_processes = open(os.path.join(os.path.dirname(__file__), "whitelist.txt")).read().splitlines()
        self.pid_queue = pid_queue
        self.safe_pid = set()
        
    def run(self):
        """
        Main monitoring loop that continuously checks for new processes.
        
        Detects new processes, terminates unauthorized ones, and reports them
        through the queue to the main proctoring system.
        """
        print("Process monitoring started\n")
        previous_processes = self._get_user_processes()
        self.known_pids = set()  # Track PIDs we've already reported
        
        while True:
            time.sleep(1)  # Check processes every second
            current_processes = self._get_user_processes()
            
            # Compare with previous snapshot to detect changes
            started, stopped = self._compare_processes(previous_processes, current_processes)

            # Update safe PIDs from internal process queue
            while not self.pid_queue.empty():
                self.safe_pid.add(self.pid_queue.get())
            
            # Handle newly started processes
            if started:
                for name, pidarray in started.items():
                    # Check if process is not in the whitelist
                    if len([safe for safe in self.safe_processes if safe in name]) < 1:
                        for pid in pidarray:
                            # Skip if process is part of the proctoring system or already known
                            if pid['pid'] in self.safe_pid or pid['pid'] in self.known_pids:
                                continue
                            # Terminate unauthorized process
                            self._kill_process(pid['pid'])
                            self.known_pids.add(pid['pid'])
                            # Report the violation
                            self.queue.put({
                                'type': 'new_process',
                                'timestamp': datetime.now(),
                                'pid': pid['pid'],
                                'name': name
                            })
                
            # Update previous state for next comparison
            previous_processes = current_processes
            
    def _get_user_processes(self):
        """
        Gets all processes belonging to the current user.
        
        Returns:
            dict: Dictionary of processes grouped by name, with process details.
        """
        processes_dict = {}
        for process in psutil.process_iter(['pid', 'name', 'username']):
            try:
                if process.info['username'] == self.username:
                    proc_name = process.info['name']
                    proc_info = {
                        "pid": process.info['pid'],
                        "username": process.info['username']
                    }
                    # Group processes by name
                    if proc_name not in processes_dict:
                        processes_dict[proc_name] = []
                    processes_dict[proc_name].append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes_dict

    def _compare_processes(self, old, new):
        """
        Compares two process snapshots to detect started and stopped processes.
        
        Args:
            old (dict): Previous process snapshot.
            new (dict): Current process snapshot.
            
        Returns:
            tuple: Dictionaries of started and stopped processes.
        """
        started = {}
        stopped = {}

        # Detect started processes
        for name, new_list in new.items():
            old_list = old.get(name, [])
            new_pids = {proc['pid'] for proc in new_list}
            old_pids = {proc['pid'] for proc in old_list}
            added_pids = new_pids - old_pids
            if added_pids:
                started[name] = [proc for proc in new_list if proc['pid'] in added_pids]

        # Detect stopped processes
        for name, old_list in old.items():
            new_list = new.get(name, [])
            old_pids = {proc['pid'] for proc in old_list}
            new_pids = {proc['pid'] for proc in new_list}
            removed_pids = old_pids - new_pids
            if removed_pids:
                stopped[name] = [proc for proc in old_list if proc['pid'] in removed_pids]

        return started, stopped
    
    def _kill_process(self, pid):
        """
        Terminates a process and all its children recursively.
        
        Args:
            pid (int): Process ID to terminate.
        """
        try:
            process = psutil.Process(pid)
            # Recursively terminate child processes first
            for subprocess in process.children(recursive=True):
                self._kill_process(subprocess.pid)
            # Terminate the main process if it's still running
            if process.is_running: process.kill()
        except Exception as e:
            print(f"Couldn't gracefully terminate PID: {pid}")