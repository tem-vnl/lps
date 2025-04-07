"""
    Gazetracking class
"""

import os
import cv2 as cv
import mediapipe as mp
import numpy as np
import math
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class Gaze(object):
    @staticmethod
    def theta_phi_to_unit_vector(theta, phi):
        return (np.sin(phi * np.pi / 180)*np.cos(theta * np.pi / 180), np.sin(phi * np.pi / 180)*np.sin(theta * np.pi / 180), np.cos(theta * np.pi / 180))

    @staticmethod
    def lm_to_int_2d_add(lm, v, w, h):
        return (int((lm.x + v[0])*w), int((lm.y + v[1])*h))

    @staticmethod
    def lm_to_int_2d(lm, w, h):
        return (int(lm.x*w), int(lm.y*h))
    
    @staticmethod
    def lm_vector_from_to(a, b):
        return [a.x - b.x, a.y - b.y, a.z - b.z]

    @staticmethod
    def unit_vector_cross(v1, v2):
        normal = np.cross(v1, v2)
        return normal / np.linalg.norm(normal)
    
    def __init__(self, queue, demo = False):
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
        self._track = {
            "lm_199": None,
            "lm_156": None,
            "lm_168": None,
            "lm_33": None,
            "lm_27": None,
            "lm_468": None,
            "lm_362": None,
            "lm_257": None,
            "lm_473": None,
            "lm_10": None,
            "lm_383": None,
            "lm_133": None,
            "lm_230": None,
            "lm_263": None,
            "lm_450": None,
            "vf_vector": None,
            "hf_vector": None,
            "f_normal": None,
            "lew_vector": None,
            "leh_vector": None,
            "liw_vector": None,
            "lih_vector": None,
            "lgh_vector": None,
            "lgv_vector": None,
            "le_normal": None,
            "rew_vector": None,
            "reh_vector": None,
            "riw_vector": None,
            "rih_vector": None,
            "rgh_vector": None,
            "rgv_vector": None,
            "re_normal": None,
            "e_normal": None,
            "g_normal": None
        }
        self._timer = None
        self._queue = queue
        self.active = True

        if not self._feed.isOpened():
            RuntimeError('Could not open videostream')
            exit

        while self.active:
            _, self._frame = self._feed.read()
            self._analyze()
            if self._track["g_normal"]:
                self._time()
                if demo:
                    self.visualise()

            cv.waitKeyEx(1)
        
        self._feed.release()
        cv.destroyAllWindows()

    def _time(self):

        if abs(self._track["g_normal"][0]) > 0.15:
            if not self._gazeaway:
                self._timer = time.time()
            self._gazeaway = True
        elif self._gazeaway:
            self._report()
            self._gazeaway = False

    def _report(self):
        tdiff = time.time() - self._timer
        if tdiff > 0.25:
            self._queue.put(tdiff)

    def _analyze(self):
        frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=self._frame)
        self._result = self._detector.detect(frame)
        # Head tracking points: 156 (left eye corner), 168 (center of face), 383 (right eye corner), 199 (center chin), 10 (center forehead)
        # Left Eye tracking points: 33 (outer edge), 133 (inner edge), 27 (top), 230 (bottom)
        # Right Eye tracking points: 263 (outer edge), 362 (inner edge), 257 (top), 450 (bottom)
        # Center iris: 468 (left), 473 (right)

        if self._result.face_landmarks:
            for lm in self._result.face_landmarks:
                for i in [199, 156, 168, 33, 27, 468, 362, 257, 473, 10, 383, 133, 230, 263, 450]:
                    self._track["lm_" + str(i)] = lm[i]
                # Calculate difference between depth in face to identify face angle
                self._track["vf_vector"] = self.lm_vector_from_to(self._track["lm_10"], self._track["lm_199"])
                self._track["hf_vector"] = self.lm_vector_from_to(self._track["lm_383"], self._track["lm_156"])
                self._track["f_normal"] = self.unit_vector_cross(self._track["hf_vector"], self._track["vf_vector"])

                # Rough gaze vector of left eye
                self._track["lew_vector"] = self.lm_vector_from_to(self._track["lm_133"], self._track["lm_33"])
                self._track["leh_vector"] = self.lm_vector_from_to(self._track["lm_230"], self._track["lm_27"])
                self._track["liw_vector"] = self.lm_vector_from_to(self._track["lm_468"], self._track["lm_33"])
                self._track["lih_vector"] = self.lm_vector_from_to(self._track["lm_468"], self._track["lm_27"])
                self._track["lgh_vector"] = (((self._track["liw_vector"][0] / self._track["lew_vector"][0]) - 0.4) / 0.2) * 90
                self._track["lgv_vector"] = (((self._track["lih_vector"][1] / self._track["leh_vector"][1]) - 0.38) / 0.05) * 90
                self._track["le_normal"] = self.theta_phi_to_unit_vector(self._track["lgv_vector"], self._track["lgh_vector"])

                # Rough gaze vector of right eye
                self._track["rew_vector"] = self.lm_vector_from_to(self._track["lm_263"], self._track["lm_362"])
                self._track["reh_vector"] = self.lm_vector_from_to(self._track["lm_257"], self._track["lm_450"])
                self._track["riw_vector"] = self.lm_vector_from_to(self._track["lm_473"], self._track["lm_263"])
                self._track["rih_vector"] = self.lm_vector_from_to(self._track["lm_473"], self._track["lm_257"])
                self._track["rgh_vector"] = (((self._track["riw_vector"][0] / self._track["rew_vector"][0]) - 0.4) / 0.2) * 90
                self._track["rgv_vector"] = -(((self._track["rih_vector"][1] / self._track["reh_vector"][1]) - 0.38) / 0.05) * 90
                self._track["re_normal"] = self.theta_phi_to_unit_vector(self._track["rgv_vector"], self._track["rgh_vector"])
                
                # Average left/right eye direction
                self._track["e_normal"] = tuple( i / 2 for i in (self._track["le_normal"] + self._track["re_normal"]))

                # Calculate vector based on face-normal +/- average eye normal
                self._track["g_normal"] = tuple( i / 2 for i in (self._track["e_normal"][0:3] + self._track["f_normal"]))

    def close(self):
        self.active = False

    def visualise(self):
        h, w = self._frame.shape[:2]
        overlay = self._frame.copy()

        # Visualize
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_199"], w, h), self.lm_to_int_2d_add(self._track["lm_199"], self._track["vf_vector"], w, h), (255,255,0, 0.1), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_156"], w, h), self.lm_to_int_2d_add(self._track["lm_156"], self._track["hf_vector"], w, h), (255,255,0, 0.1), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_168"], w, h), self.lm_to_int_2d_add(self._track["lm_168"], self._track["f_normal"], w, h), (205,105,105, 0.1), 2, 1, 0)

        cv.line(overlay, self.lm_to_int_2d(self._track["lm_33"], w, h), self.lm_to_int_2d_add(self._track["lm_33"], self._track["lew_vector"], w, h), (255,255,0), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_27"], w, h), self.lm_to_int_2d_add(self._track["lm_27"], self._track["leh_vector"], w, h), (255,255,0), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_468"], w, h), self.lm_to_int_2d_add(self._track["lm_27"], self._track["e_normal"], w, h), (255,255,0), 1, 1, 0)

        cv.line(overlay, self.lm_to_int_2d(self._track["lm_362"], w, h), self.lm_to_int_2d_add(self._track["lm_362"], self._track["rew_vector"], w, h), (255,255,0), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_450"], w, h), self.lm_to_int_2d_add(self._track["lm_450"], self._track["reh_vector"], w, h), (255,255,0), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_473"], w, h), self.lm_to_int_2d_add(self._track["lm_473"], self._track["e_normal"], w, h), (255,255,0), 1, 1, 0)

        result = cv.addWeighted(overlay, 0.3, self._frame, 1, 0)
        cv.line(result, self.lm_to_int_2d(self._track["lm_168"], w, h), self.lm_to_int_2d_add(self._track["lm_168"], self._track["g_normal"], w, h), (205,100,205, 0.1), 2, 1, 0)

        if (self._gazeaway):
            cv.putText(result, "GAZEAWAY DETECTED", (35, 35), cv.FONT_HERSHEY_DUPLEX, 1, (147, 58, 31), 2)
        else:
            cv.putText(result, "FOCUSING", (35, 35), cv.FONT_HERSHEY_DUPLEX, 1, (147, 58, 31), 2)
        cv.putText(result, f"XDIFF: {abs(self._track["g_normal"][0])}", (35, 65), cv.FONT_HERSHEY_DUPLEX, 0.75, (147, 58, 31), 2)
        cv.putText(result, f"YDUFF: {abs(self._track["g_normal"][1])}", (35, 95), cv.FONT_HERSHEY_DUPLEX, 0.75, (147, 58, 31), 2)
        
        cv.imshow('_feed', result)