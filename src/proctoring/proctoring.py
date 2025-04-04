"""
    Proctoring software class
"""

from proctoring.eyetracker import Eyetracker

class Proctoring(object):
    def __init__(self):
        eyetracker = Eyetracker()