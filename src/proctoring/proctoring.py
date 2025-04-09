"""
    Proctoring software class
"""

from proctoring.gaze import Gaze
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
        self.gaze_queue = Queue()

        gaze = Process(target=self.run_gaze, args=(self.gaze_queue, demo,))
        gaze.start()
        gaze_recieve = Process(target=self.listen_for_gaze)
        gaze_recieve.start()
    
    def run_gaze(self, queue, demo):
        gaze_instance = Gaze(queue, demo)
        gaze_instance.run()

    def listen_for_gaze(self):
        while True:
            if not self.gaze_queue.empty():
                message = self.gaze_queue.get()
                print(f"Gazeaway: {message:.2f}")