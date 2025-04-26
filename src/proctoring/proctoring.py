"""
    Proctoring software class
"""

from proctoring.gaze import Gaze
from proctoring.processes import ProcessMonitor
from proctoring.browser import Browser
from multiprocessing import Process, Queue
from plyer import notification
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime
import time

class Proctoring:
    """
    A class to handle proctoring functionality.

    Attributes:
        demo (bool): Whether the program is running in demo mode.
    """

    APP_NAME = "Proctoring system"

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

        self._processes = {
            "gaze": None,
            "gaze_recieve": None,
            "process_monitor": None,
            "process_monitor_recieve": None,
            "browser": None
        }

        self._total_gazeaway = 0.0
        self._start_time = None
        self._process_entries = {
            'initial': set(),
            'new': []
        }

        self.running = False

    def start_exam(self):
        if self.running == True: return
        self._start_time = datetime.now()
        self._processes["gaze"] = Process(target=self._run_gaze, args=(self._gaze_queue,))
        self._processes["gaze_recieve"] = Process(target=self._listen_for_gaze)
        self._processes["process_monitor"] = Process(target=self._run_process_monitor, args=(self._process_queue,))
        self._processes["process_monitor_recieve"] = Process(target=self._listen_for_processes)
        self._processes["browser"] = Process(target=self._run_browser, args=(self._browser_queue,))

        for _, process in self._processes.items():
            process.start()

        self.running = True

    def end_exam(self):
        if self.running == False: return
        
        # Signal processes to stop and wait for final data
        self._browser_queue.put("STOP")
        time.sleep(1)  # Give processes time to cleanup and send final data
        
        # Process any remaining messages in queues
        while not self._gaze_queue.empty():
            msg = self._gaze_queue.get()
            self._total_gazeaway += msg
            
        while not self._process_queue.empty():
            msg = self._process_queue.get()
            if isinstance(msg, dict) and msg.get('type') == 'new_process':
                entry = (msg['timestamp'], msg['pid'], msg['name'])
                self._process_entries['new'].append(entry)
            
        for name, process in self._processes.items():
            process.terminate()
            self._processes[name] = None

        self.generate_report("exam_report.pdf")
        self.running = False
    
    def _run_gaze(self, queue):
        Gaze(queue, self._demo).run()

    def _run_process_monitor(self, queue):
        ProcessMonitor(queue).run()

    def _run_browser(self, queue):
        Browser(queue).run()

    def _listen_for_gaze(self):
        while True:
            if not self._gaze_queue.empty():
                msg = self._gaze_queue.get()
                self._total_gazeaway += msg
                title = "Gazeaway"
                message=f"Identified user gazeaway for: {msg:.2f}s"
                self._notify(title, message)

    def _listen_for_processes(self):
        while True:
            if not self._process_queue.empty():
                msg = self._process_queue.get()
                if isinstance(msg, dict) and msg.get('type') == 'new_process':
                    entry = (msg['timestamp'], msg['pid'], msg['name'])
                    self._process_entries['new'].append(entry)
                    title = "Process identified"
                    message = f"New process: {msg['name']} (PID: {msg['pid']})"
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

    def generate_report(self, filename="exam_report.pdf"):
        """Generate a PDF report with exam monitoring results."""
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
        c.drawString(inch, y, f"Exam Start Time: {self._start_time}")
        y -= 0.3*inch
        c.drawString(inch, y, f"Total Time Gazing Away: {self._total_gazeaway:.2f} seconds")
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
        for timestamp, pid, name in self._process_entries['new']:
            if y < inch:
                page += 1
                new_page()
            
            c.drawString(inch, y, timestamp.strftime("%H:%M:%S"))
            c.drawString(3*inch, y, str(pid))
            c.drawString(4*inch, y, name)
            y -= 0.25*inch
        
        c.save()