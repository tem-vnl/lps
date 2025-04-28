import time
import math
from datetime import datetime
from multiprocessing import Process, Queue, Value, Manager

import psutil
from plyer import notification

"""
    Proctoring software class
"""

from proctoring.gaze import Gaze
from proctoring.processes import ProcessMonitor
from proctoring.browser import Browser
from proctoring.report import Report

class Proctoring:
    """
    A class to handle proctoring functionality.

    Attributes:
        demo (bool): Whether the program is running in demo mode.
    """

    APP_NAME = "Proctoring system"
    INVALID_AT_STARTUP = ["chrome"]

    def __init__(self, demo: bool = False):
        """
        Initialize the Proctoring system.

        Args:
            demo (bool): Run in demo mode if True.
        """
        self._demo = demo 

        self._manager = Manager()
        self._process_entries = self._manager.dict({
            'initial': set(),
            'new': self._manager.list()
        })

        self._gaze_queue = Queue()
        self._process_queue = Queue()
        self._browser_queue = Queue()
        self._internal_pid_queue = Queue()
        self._stop_monitoring = False  # Add this line

        self._processes = {
            "gaze": None,
            "gaze_recieve": None,
            "process_monitor": None,
            "process_monitor_recieve": None,
            "browser": None
        }

        self._time = {
            "time": Value('d', 0.0),
            "start": None,
            "end": None,
            "total_gazeaway": 0.0,
            "reported_time": 0
        }

        self.running = False

    def start_exam(self):
        if self.running == True: return
        self._time['start'] = datetime.now()
        
        # Store just process names initially
        self._process_entries['initial'] = {
            p.info['name'].lower() for p in psutil.process_iter(['name'])
        }
        
        self._processes["browser"] = Process(target=self._run_browser, args=(self._browser_queue, self._internal_pid_queue,))
        self._processes["gaze"] = Process(target=self._run_gaze, args=(self._gaze_queue,))
        self._processes["gaze_recieve"] = Process(target=self._listen_for_gaze)
        self._processes["process_monitor"] = Process(target=self._run_process_monitor, args=(self._process_queue,self._internal_pid_queue))
        self._processes["process_monitor_recieve"] = Process(target=self._listen_for_processes)

        for _, process in self._processes.items():
            process.start()

        self.running = True

    def end_exam(self):
        if not self.running: return
        
        self._time["end"] = datetime.now()
        
        self._browser_queue.put("STOP")
        time.sleep(1)

        for name, process in self._processes.items():
            if process:
                process.terminate()
                process.join(timeout=1)
                self._processes[name] = None

        Report.generate_report(self._time, list(self._process_entries['new']), "exam_report.pdf")
        self.running = False

    def _drain_queues(self):
        # Process any remaining gaze data
        while not self._gaze_queue.empty():
            try:
                msg = self._gaze_queue.get_nowait()
                with self._time["time"].get_lock():
                    self._time["time"].value += msg
            except:
                break

        # Process any remaining process data
        while not self._process_queue.empty():
            try:
                msg = self._process_queue.get_nowait()
                if isinstance(msg, dict) and msg.get('type') == 'new_process':
                    entry = (msg['timestamp'], msg['pid'], msg['name'])
                    if msg['name'].lower() not in self._process_entries['initial']:
                        self._process_entries['new'].append(entry)
            except:
                break

    def _run_gaze(self, queue):
        Gaze(queue, self._demo)

    def _run_browser(self, queue, pid_queue):
        Browser(queue, pid_queue).run()

    def _run_process_monitor(self, queue, pid_queue):
        ProcessMonitor(queue, pid_queue).run()

    def _listen_for_gaze(self):
        while not self._stop_monitoring:  # Modified condition
            if not self._gaze_queue.empty():
                with self._time["time"].get_lock():
                    self._time["time"].value += self._gaze_queue.get()
                total_minutes = math.floor(self._time["time"].value / 60)
                
                if total_minutes > self._time['reported_time']:
                    self._time['reported_time'] = total_minutes
                    title = "Gazeaway"
                    message=f"Warning: Time spent not looking at screen has been logged, total time logged: {total_minutes:.2f} minutes"
                    self._notify(title, message)
        
    def _listen_for_processes(self):
        while True:
            if not self._process_queue.empty():
                msg = self._process_queue.get()
                if isinstance(msg, dict) and msg.get('type') == 'new_process':
                    # Check if this PID existed at start with the same name
                    if msg['name'].lower() not in self._process_entries['initial']:
                        self._process_entries['new'].append((msg['timestamp'], msg['pid'], msg['name']))
                        title = "Process identified"
                        message = f"Warning: Process not allowed during exam identified: {msg['name']}"
                        self._notify(title, message)
            time.sleep(0.1)

    def _notify(self, title, message):
        notification.notify(
            app_name = self.APP_NAME,
            app_icon = '',
            title = title,
            message = message,
            timeout = 3,
            toast = False
        )

    def valid_startup(self):
        running = [name for name in self.INVALID_AT_STARTUP if self._check_running_process(name)]
        return len(running) < 1, running
        
 
    def _check_running_process(self, name):
        for process in psutil.process_iter():
            try:
                if name == process.name().lower() and process.is_running:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False