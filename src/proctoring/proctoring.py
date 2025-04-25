"""
    Proctoring software class
"""

from proctoring.gaze import Gaze
from proctoring.processes import ProcessMonitor
from proctoring.browser import Browser
from multiprocessing import Process, Queue

class Proctoring:
    """
    A class to handle proctoring functionality.

    Attributes:
        demo (bool): Whether the program is running in demo mode.
    """

    def __init__(self, demo: bool = False):
        """
        Initialize the Proctoring system.

        Args:
            demo (bool): Run in demo mode if True.
        """
        # Initialize queues
        self.gaze_queue = Queue()
        self.process_queue = Queue()
        self.internal_pid_queue = Queue()
        
        # Start gaze monitoring
        gaze = Process(target=self.run_gaze, args=(self.gaze_queue, demo,))
        gaze_receive = Process(target=self.listen_for_gaze)
        
        # Start process monitoring
        process_monitor = Process(target=self.run_process_monitor, args=(self.process_queue,self.internal_pid_queue))
        process_receive = Process(target=self.listen_for_processes)
        
        # Start browser
        browser = Process(target=self.run_browser, args=(self.internal_pid_queue,))
        
        # Start all processes
        for p in [gaze, gaze_receive, process_monitor, process_receive, browser]:
            p.start()

    def run_gaze(self, queue, demo):
        gaze_instance = Gaze(queue, demo)
        gaze_instance.run()

    def listen_for_gaze(self):
        while True:
            if not self.gaze_queue.empty():
                message = self.gaze_queue.get()
                print(f"Gazeaway: {message:.2f}")
                
    def run_process_monitor(self, queue, pid_queue):
        monitor = ProcessMonitor(queue, pid_queue)
        monitor.run()
        
    def listen_for_processes(self):
        while True:
            if not self.process_queue.empty():
                message = self.process_queue.get()
                print(f"Process change: {message}")
                
    def run_browser(self, pid_queue):
        browser = Browser(pid_queue)
        browser.run()