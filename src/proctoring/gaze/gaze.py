"""
    Gazetracking class
"""

import os
import cv2 as cv
import mediapipe as mp
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class Gaze(object):
    def __init__(self):
        self._feed = cv.VideoCapture(0)
        self._frame = None
        self._base_options = python.BaseOptions(model_asset_path=os.path.dirname(__file__) + '/models/face_landmarker_v2_with_blendshapes.task')
        self._options = vision.FaceLandmarkerOptions(
            base_options=self._base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1,
            running_mode=mp.tasks.vision.RunningMode.IMAGE
        )
        self._detector = vision.FaceLandmarker.create_from_options(self._options)
        self._result = None
        self._gazeaway = False
        self._timer = None
        self.active = True

        if not self._feed.isOpened():
            RuntimeError('Could not open videostream')
            exit

        while self.active:
            _, self._frame = self._feed.read()
            self._analyze()
            # self.visualise()

            if cv.waitKeyEx(1) == 27:
                break
        
        self._feed.release()
        cv.destroyAllWindows()

    def _report(self):
        print("Gazeaway for {elapsed:.3f}s".format(elapsed = time.time() - self._timer))

    def _analyze(self):
        frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=self._frame)
        self._result = self._detector.detect(frame)
        h, w = self._frame.shape[:2]
        # Head track: 156 (left eye corner), 168 (center of face), 383 (right eye corner)
        # Eye track: 133 (left eye inner corner), 33 (left eye outer corner), 362 (right eye inner corner), 263 (right eye outer corner)
        # Center iris: 468 (left), 473 (right) 

        if self._result.face_landmarks:
            for landmarks in self._result.face_landmarks:
                # Calculate difference between depth in face to identify face angle
                face_left_depth, face_right_depth = landmarks[168].z - landmarks[156].z, landmarks[168].z - landmarks[383].z
                face_width = (landmarks[156].x - landmarks[383].x)**2 + (landmarks[156].y - landmarks[383].y)**2
                face_angle = ((face_left_depth - face_right_depth) * 90) / (face_width * 16)

                # Analyze eyes
                left_eye_width = landmarks[133].x - landmarks[33].x
                left_iris_percentage = (landmarks[468].x - landmarks[33].x) / left_eye_width
                left_iris_angle = (left_iris_percentage - .4) * 140

                right_eye_width = landmarks[362].x - landmarks[263].x
                right_iris_percentage = (landmarks[473].x - landmarks[263].x) / right_eye_width
                right_iris_angle = -(right_iris_percentage - .4) * 140

                average_iris_angle = (left_iris_angle + right_iris_angle) / 2

                # Estimate gaze angle
                gaze_angle = face_angle + average_iris_angle
                if (abs(gaze_angle) > 15):
                    if not self._gazeaway:
                        self._timer = time.time()
                    self._gazeaway = True
                elif self._gazeaway:
                    self._report()
                    self._gazeaway = False

    
    def close(self):
        self.active = False

    def visualise(self):
        if (self._gazeaway):
            cv.putText(self._frame, "GAZEAWAY DETECTED", (90, 60), cv.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)
        else:
            cv.putText(self._frame, "FOCUSING", (90, 60), cv.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)
        cv.imshow('_feed', self._frame)