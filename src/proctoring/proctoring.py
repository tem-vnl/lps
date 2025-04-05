"""
    Proctoring software class
"""

from proctoring.gaze import Gaze
from multiprocessing import Process

class Proctoring(object):
    def __init__(self):

        gaze = Process(target=Gaze)
        gaze.start()