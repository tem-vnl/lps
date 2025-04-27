"""
    Proctoring software class
"""

from proctoring.gaze import Gaze
from proctoring.processes import ProcessMonitor
from proctoring.browser import Browser
from multiprocessing import Process, Queue
from plyer import notification
import psutil
import time
import math

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

        self._gaze_queue = Queue()
        self._process_queue = Queue()
        self._browser_queue = Queue()
        self._internal_pid_queue = Queue()

        self._gaze_time = 0
        self._reported_time = 0

        self._processes = {
            "gaze": None,
            "gaze_recieve": None,
            "process_monitor": None,
            "process_monitor_recieve": None,
            "browser": None
        }

        self.running = False

    def start_exam(self):
        if self.running == True: return
        self._processes["gaze"] = Process(target=self._run_gaze, args=(self._gaze_queue,))
        self._processes["gaze_recieve"] = Process(target=self._listen_for_gaze)
        self._processes["process_monitor"] = Process(target=self._run_process_monitor, args=(self._process_queue,self._internal_pid_queue))
        self._processes["process_monitor_recieve"] = Process(target=self._listen_for_processes)
        self._processes["browser"] = Process(target=self._run_browser, args=(self._browser_queue, self._internal_pid_queue,))

        for _, process in self._processes.items():
            process.start()

        self.running = True

    def end_exam(self):
        if self.running == False: return
        
        # Signal browser to close and wait for it to process
        self._browser_queue.put("STOP")
        time.sleep(1)  # Give browser time to cleanup
        
        for name, process in self._processes.items():
            process.terminate()
            self._processes[name] = None

        self.running = False
    
    def _run_gaze(self, queue):
        Gaze(queue, self._demo).run()

    def _run_browser(self, queue, pid_queue):
        Browser(queue, pid_queue).run()

    def _run_process_monitor(self, queue, pid_queue):
        ProcessMonitor(queue, pid_queue).run()

    def _listen_for_gaze(self):
        while True:
            if not self._gaze_queue.empty():
                self._gaze_time += self._gaze_queue.get()
                total_minutes = math.floor(self._gaze_time / 60)
                print(self._gaze_time, total_minutes)
                if total_minutes > self._reported_time:
                    self._reported_time = total_minutes
                    title = "Gazeaway"
                    message=f"Warning: Time spent not looking at screen has been logged, total time logged: {total_minutes} minutes"
                    self._notify(title, message)
        
    def _listen_for_processes(self):
        while True:
            if not self._process_queue.empty():
                msg = self._process_queue.get()
                title = "Process identified"
                message=f"Warning: Process not allowed during exam identified: {msg}"
                self._notify(title, message)

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