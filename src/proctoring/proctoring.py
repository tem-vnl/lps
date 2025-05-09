import time
import math
from datetime import datetime
from multiprocessing import Process, Queue, Value, Manager

import psutil
from plyer import notification

import tkinter as tk
from tkinter import messagebox

"""
    Proctoring software class
"""

from proctoring.gaze import Gaze
from proctoring.processes import ProcessMonitor
from proctoring.browser import Browser
from proctoring.report import Report

class Proctoring:
    """
    A class to handle proctoring functionality during exams.

    Coordinates various monitoring systems including gaze tracking, process monitoring,
    and browser lockdown through multiprocessing. Collects data for reports and 
    handles notification of potential violations.

    Attributes:
        _demo (bool): Whether the program is running in demo mode.
        _manager (Manager): Multiprocessing manager for shared objects.
        _process_entries (dict): Dictionary to track initial and new processes.
        _queues (dict): Dictionary of queues for handling process messaging.
        _processes (dict): Dictionary of monitoring process objects.
        _time (dict): Dictionary to track timing information.
        running (bool): Indicates whether an exam is currently running.
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

        # Set up multiprocessing manager and shared data structures
        self._manager = Manager()
        self._process_entries = self._manager.dict({
            'initial': set(),
            'new': self._manager.list()
        })

        # Create communication queues for the monitoring processes
        self._queues = {
            "gaze": Queue(),
            "process": Queue(),
            "to_browser": Queue(),
            "from_browser": Queue(),
            "internal_pid": Queue()
        }

        # Dictionary to store process objects for different monitoring components
        self._processes = {
            "gaze": None,
            "gaze_recieve": None,
            "process_monitor": None,
            "process_monitor_recieve": None,
            "browser": None
        }

        # Dictionary to track timing information for the exam session
        self._time = {
            "time": Value('d', 0.0),  # Shared value for gaze-away time
            "start": None,            # Exam start timestamp
            "end": None,              # Exam end timestamp
            "total_gazeaway": 0.0,    # Total gaze-away time
            "reported_time": 0        # Last reported gaze-away time in minutes
        }

        self.running = False

    def start_exam(self):
        """
        Starts an exam session by initializing and launching all monitoring processes.
        
        Records the start time, captures initial system state, and launches processes
        for gaze tracking, process monitoring, and browser lockdown.
        """
        if self.running == True: return
        self._time['start'] = datetime.now()
        
        # Store just process names initially to detect new processes later
        self._process_entries['initial'] = {
            p.info['name'].lower() for p in psutil.process_iter(['name'])
        }
        
        # Initialize and start all monitoring processes
        self._processes["browser"] = Process(target=self._run_browser, args=(self._queues["to_browser"], self._queues["from_browser"], self._queues["internal_pid"],))
        self._processes["gaze"] = Process(target=self._run_gaze, args=(self._queues["gaze"],))
        self._processes["gaze_recieve"] = Process(target=self._listen_for_gaze)
        self._processes["process_monitor"] = Process(target=self._run_process_monitor, args=(self._queues["process"],self._queues["internal_pid"]))
        self._processes["process_monitor_recieve"] = Process(target=self._listen_for_processes)

        # Start browser process and setup loop for awaiting initial load
        self._processes["browser"].start()
        timeout_counter = 0
        while True:
            if timeout_counter > 20:
                self._show_error("Start Error", 
                    "Exam couldn't start because of a problem with the browser environment or network.")
                return
            timeout_counter += 1
            try:
                browser_message = self._queues["from_browser"].get_nowait()
                if browser_message == "navigated": break
            except:
                time.sleep(1)
        
        # Start all other test processes
        for name, process in self._processes.items():
            if name == "browser": continue
            process.start()

        self.running = True

    def end_exam(self, force=False):
        """
        Ends an exam session by stopping all monitoring processes.
        
        Records the end time, stops all monitoring processes, and generates
        a report of the exam session.
        """
        if not self.running and not force: return
        
        self._time["end"] = datetime.now()
        
        # Send stop signal to browser process
        self._queues["to_browser"].put("STOP")
        time.sleep(1)

        # Terminate all monitoring processes
        for name, process in self._processes.items():
            if process:
                process.terminate()
                process.join(timeout=1)
                self._processes[name] = None

        # Generate exam report with collected data
        Report.generate_report(self._time, list(self._process_entries['new']), "exam_report")
        self.running = False

    def _drain_queues(self):
        """
        Processes any remaining data in monitoring queues.
        
        Ensures all monitoring data is properly processed before shutting down,
        including remaining gaze and process data.
        """
        # Process any remaining gaze data
        while not self._queues["gaze"].empty():
            try:
                msg = self._queues["gaze"].get_nowait()
                with self._time["time"].get_lock():
                    self._time["time"].value += msg
            except:
                break

        # Process any remaining process data
        while not self._queues["process"].empty():
            try:
                msg = self._queues["process"].get_nowait()
                if isinstance(msg, dict) and msg.get('type') == 'new_process':
                    entry = (msg['timestamp'], msg['pid'], msg['name'])
                    if msg['name'].lower() not in self._process_entries['initial']:
                        self._process_entries['new'].append(entry)
            except:
                break

    def _run_gaze(self, queue):
        """
        Starts the gaze tracking component.
        
        Args:
            queue (Queue): Queue for receiving gaze tracking data.
        """
        Gaze(queue, self._demo)

    def _run_browser(self, to_queue, from_queue, pid_queue):
        """
        Starts the browser monitoring component.
        
        Args:
            queue (Queue): Queue for sending commands to the browser monitor.
            pid_queue (Queue): Queue for sharing internal process IDs.
        """
        Browser(to_queue, from_queue, pid_queue).run()

    def _run_process_monitor(self, queue, pid_queue):
        """
        Starts the process monitoring component.
        
        Args:
            queue (Queue): Queue for receiving process monitoring data.
            pid_queue (Queue): Queue for sharing internal process IDs.
        """
        ProcessMonitor(queue, pid_queue).run()

    def _listen_for_gaze(self):
        """
        Continuous loop to process gaze tracking data from the queue.
        
        Monitors time spent looking away from the screen and sends notifications
        when significant time is accumulated.
        """
        while True:
            if not self._queues["gaze"].empty():
                # Update the time value with new gaze-away duration
                with self._time["time"].get_lock():
                    self._time["time"].value += self._queues["gaze"].get()
                total_minutes = math.floor(self._time["time"].value / 60)
                
                # Send notification when a new minute threshold is crossed
                if total_minutes > self._time['reported_time']:
                    self._time['reported_time'] = total_minutes
                    title = "Gazeaway"
                    message=f"Warning: Time spent not looking at screen has been logged, total time logged: {total_minutes:.2f} minutes"
                    self._notify(title, message)
        
    def _listen_for_processes(self):
        """
        Continuous loop to process monitoring data from the process queue.
        
        Detects new processes that were not running at exam start and logs them
        as potential violations.
        """
        while True:
            if not self._queues["process"].empty():
                msg = self._queues["process"].get()
                if isinstance(msg, dict) and msg.get('type') == 'new_process':
                    # Check if this process is new (wasn't running at start)
                    if msg['name'].lower() not in self._process_entries['initial']:
                        self._process_entries['new'].append((msg['timestamp'], msg['pid'], msg['name']))
                        title = "Process identified"
                        message = f"Warning: Process not allowed during exam identified: {msg['name']}"
                        self._notify(title, message)
            time.sleep(0.1)

    def _notify(self, title, message):
        """
        Sends a desktop notification to the user.
        
        Args:
            title (str): Title of the notification.
            message (str): Body text of the notification.
        """
        notification.notify(
            app_name = self.APP_NAME,
            app_icon = '',
            title = title,
            message = message,
            timeout = 3,
            toast = False
        )

    def valid_startup(self):
        """
        Checks if the system is in a valid state to start an exam.
        
        Verifies that none of the prohibited applications are running
        before allowing the exam to start.
        
        Returns:
            tuple: (is_valid, list_of_prohibited_running_processes)
        """
        running = [name for name in self.INVALID_AT_STARTUP if self._check_running_process(name)]
        return len(running) < 1, running
        
 
    def _check_running_process(self, name):
        """
        Checks if a process with the given name is currently running.
        
        Args:
            name (str): Name of the process to check.
            
        Returns:
            bool: True if the process is running, False otherwise.
        """
        for process in psutil.process_iter():
            try:
                if name == process.name().lower() and process.is_running:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    def _show_error(self, title, message):
        """
        Shows an error message box using tkinter.
        
        Args:
            title (str): Title of the error dialog
            message (str): Error message to display
        """
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showerror(title, message)
        root.destroy()