"""
    Proctoring software class
"""

from proctoring.gaze import Gaze
from proctoring.processes import ProcessMonitor
from proctoring.browser import Browser
from multiprocessing import Process, Queue, Value, Manager
from plyer import notification
import psutil
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime
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

        self._manager = Manager()
        self._process_entries = self._manager.dict({
            'initial': set(),
            'new': self._manager.list()
        })

        self._gaze_queue = Queue()
        self._gaze_time = Value('d', 0.0)  # 'd' for double precision float
        self._process_queue = Queue()
        self._browser_queue = Queue()
        self._internal_pid_queue = Queue()
        self._stop_monitoring = False  # Add this line

        self._reported_time = 0

        self._processes = {
            "gaze": None,
            "gaze_recieve": None,
            "process_monitor": None,
            "process_monitor_recieve": None,
            "browser": None
        }

        self._total_gazeaway = 0.0
        self._start_time = None

        self.running = False

    def start_exam(self):
        if self.running == True: return
        self._start_time = datetime.now()
        
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
        
        self._end_time = datetime.now()
        print(f"Ending exam. Current new processes: {list(self._process_entries['new'])}")
        
        self._browser_queue.put("STOP")
        time.sleep(1)

        for name, process in self._processes.items():
            if process:
                process.terminate()
                process.join(timeout=1)
                self._processes[name] = None

        # Convert manager list to regular list for report generation
        self._process_entries['new'] = list(self._process_entries['new'])
        
        print(f"Generating report with {len(self._process_entries['new'])} processes")
        self.generate_report("exam_report.pdf")
        self.running = False

    def _drain_queues(self):
        # Process any remaining gaze data
        while not self._gaze_queue.empty():
            try:
                msg = self._gaze_queue.get_nowait()
                with self._gaze_time.get_lock():
                    self._gaze_time.value += msg
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
                        print(f"Added process to report: {entry}")
            except:
                break

    def _run_gaze(self, queue):
        Gaze(queue, self._demo).run()

    def _run_browser(self, queue, pid_queue):
        Browser(queue, pid_queue).run()

    def _run_process_monitor(self, queue, pid_queue):
        ProcessMonitor(queue, pid_queue).run()

    def _listen_for_gaze(self):
        while not self._stop_monitoring:  # Modified condition
            if not self._gaze_queue.empty():
                with self._gaze_time.get_lock():
                    self._gaze_time.value += self._gaze_queue.get()
                total_minutes = math.floor(self._gaze_time.value / 60)
                
                if total_minutes > self._reported_time:
                    self._reported_time = total_minutes
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

    def generate_report(self, filename="exam_report.pdf"):
        """Generate a PDF report with exam monitoring results."""
        print(f"Starting report generation. Process entries: {self._process_entries['new']}")
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        y = height - inch
        page = 1

        def new_page():
            nonlocal y, page
            if page > 1:
                c.showPage()
            y = height - inch
            
            # Header on each page
            c.setFont("Helvetica-Bold", 16)
            c.drawString(inch, height - 0.5*inch, "Exam Monitoring Report")
            c.setFont("Helvetica", 8)
            c.drawString(width - 1.5*inch, height - 0.5*inch, f"Page {page}")
            y -= inch

        new_page()
        
        # Exam details
        c.setFont("Helvetica", 12)
        c.drawString(inch, y, f"Exam Start Time: {self._start_time}, End Time: {self._end_time}")
        y -= 0.3*inch
        minutes = self._gaze_time.value / 60
        c.drawString(inch, y, f"Total Time Gazing Away: {minutes:.1f} minutes ({self._gaze_time.value:.1f} seconds)")
        y -= 0.5*inch
        
        # Process list
        c.setFont("Helvetica-Bold", 14)
        c.drawString(inch, y, "New Processes During Exam:")
        y -= 0.4*inch
        
        # Column headers
        c.setFont("Helvetica-Bold", 10)
        c.drawString(inch, y, "Time")
        c.drawString(3*inch, y, "PID")
        c.drawString(4*inch, y, "Process Name")
        y -= 0.3*inch

        c.setFont("Helvetica", 10)
        print(f"Writing {len(self._process_entries['new'])} processes to report")
        for timestamp, pid, name in self._process_entries['new']:
            if y < inch:
                page += 1
                new_page()
            
            c.drawString(inch, y, timestamp.strftime("%H:%M:%S"))
            c.drawString(3*inch, y, str(pid))
            c.drawString(4*inch, y, name)
            y -= 0.25*inch
        
        c.save()