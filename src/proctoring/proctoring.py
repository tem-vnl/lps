"""
    Proctoring software class
"""

from proctoring.gaze import Gaze
from proctoring.processes import ProcessMonitor
from proctoring.browser import Browser
from multiprocessing import Process, Queue
from plyer import notification

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
        self._gaze_process = Process(target=self._run_gaze, args=(self._gaze_queue,))
        self._gaze_instance = None
        self._gaze_recieve = Process(target=self._listen_for_gaze)
        self.running = False

    def start_exam(self):
        self._gaze_process.start()
        self._gaze_recieve.start()
        self.running = True

    def end_exam(self):
        self._gaze_process.terminate()
        self._gaze_recieve.terminate()
        self.running = False
    
    def _run_gaze(self, queue):
        self._gaze_instance = Gaze(queue, self._demo)

    def _listen_for_gaze(self):
        while True:
            if not self._gaze_queue.empty():
                msg = self._gaze_queue.get()
                title = "Gazeaway"
                message=f"Identified user gazeaway for: {msg:.2f}s"
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