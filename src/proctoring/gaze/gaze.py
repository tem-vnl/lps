"""
    Gazetracking class
"""

import os
import cv2 as cv
import mediapipe as mp
import numpy as np
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class Gaze:
    """
    A class to handle gaze tracking using Mediapipe and OpenCV.

    Attributes:
        _feed (cv.VideoCapture): Video capture object for accessing the webcam.
        _frame (np.ndarray): Current video frame being processed.
        _base_options (python.BaseOptions): Base options for Mediapipe face landmarker.
        _options (vision.FaceLandmarkerOptions): Configuration options for the face landmarker.
        _detector (vision.FaceLandmarker): Mediapipe face landmarker object.
        _result (Any): Result of the face landmark detection.
        _gazeaway (bool): Indicates whether the user is looking away.
        _track (dict): Dictionary to store tracking data for facial landmarks and vectors.
        _timer (float): Timer to measure the duration of gaze-away events.
        _queue (multiprocessing.Queue): Queue for sending gaze-away duration to the main process.
        active (bool): Indicates whether the gaze tracking process is active.
    """

    LANDMARK_INDICES = [199, 156, 168, 33, 27, 468, 362, 257, 473, 10, 383, 133, 230, 263, 450]
    DEFAULT_X_THRESHOLD = 0.15
    DEFAULT_Y_THRESHOLD = 0.1
    MIN_GAZE_DURATION = 0.25

    def __init__(self, queue, demo=False):
        """
        Initializes the Gaze class.

        Args:
            queue (multiprocessing.Queue): Queue for sending gaze-away duration to the main process.
            demo (bool): Whether to run in demo mode with visualization.
        """
        self._feed = cv.VideoCapture(0)
        self._frame = None
        self._base_options = python.BaseOptions(
            model_asset_path=os.path.dirname(__file__) + "/models/face_landmarker_v2_with_blendshapes.task"
        )
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
        self._frames = 0
        self._track = {
            # Tracking data for facial landmarks and vectors
            "lm_199": None, "lm_156": None, "lm_168": None, "lm_33": None, "lm_27": None,
            "lm_468": None, "lm_362": None, "lm_257": None, "lm_473": None, "lm_10": None,
            "lm_383": None, "lm_133": None, "lm_230": None, "lm_263": None, "lm_450": None,
            "vf_vector": None, "hf_vector": None, "f_normal": None,
            "left_iris_x_space": None, "right_iris_x_space": None, "eye_x_diff": None, "eye_x_normal": None,
            "left_iris_y_space": None, "right_iris_y_space": None, "eye_y_diff": None, "eye_y_normal": None,
            "y_running_average": 0,
            "g_normal": None
        }
        self._timer = None
        self._queue = queue
        self._active = True

        if not self._feed.isOpened():
            raise RuntimeError("Could not open videostream")

        while self._active:
            _, self._frame = self._feed.read()
            self._frames += 1
            self._analyze()
            if self._track["g_normal"]:
                self._time()
                if demo:
                    self._visualise()

            cv.waitKeyEx(1)
        
        self._feed.release()
        cv.destroyAllWindows()

    def _time(self):
        """
        Tracks the duration of gaze-away events and triggers reporting.
        """
        if abs(self._track["g_normal"][0]) > self.DEFAULT_X_THRESHOLD or abs(self._track["g_normal"][1]) > self.DEFAULT_Y_THRESHOLD:
            if not self._gazeaway:
                self._timer = time.time()
            self._gazeaway = True
        elif self._gazeaway:
            self._report()
            self._gazeaway = False

    def _report(self):
        """
        Reports the duration of a gaze-away event to the main process.
        """
        tdiff = time.time() - self._timer
        if tdiff > self.MIN_GAZE_DURATION:
            try:
                self._queue.put(tdiff)
            except Exception as e:
                print(f"Error sending data to queue: {e}")

    def _analyze(self):
        """
        Analyzes the current video frame to extract facial landmarks and calculate gaze vectors.
        """
        frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=self._frame)
        self._result = self._detector.detect(frame)

        if self._result.face_landmarks:
            for lm in self._result.face_landmarks:
                """
                    Head tracking points: 156 (left eye corner), 168 (center of face), 383 (right eye corner), 199 (center chin), 10 (center forehead)
                    Left Eye tracking points: 33 (outer edge), 133 (inner edge), 27 (top), 230 (bottom)
                    Right Eye tracking points: 263 (outer edge), 362 (inner edge), 257 (top), 450 (bottom)
                    Center iris: 468 (left), 473 (right)
                    Reference: https://storage.googleapis.com/mediapipe-assets/documentation/mediapipe_face_landmark_fullsize.png
                """
                # Extract and process landmarks
                for i in self.LANDMARK_INDICES:
                    self._track["lm_" + str(i)] = lm[i]
                # Extract vertical and horizontal face vector, cross product to create normal
                self._track["vf_vector"] = self.lm_vector_from_to(self._track["lm_199"], self._track["lm_10"])
                self._track["hf_vector"] = self.lm_vector_from_to(self._track["lm_156"], self._track["lm_383"])
                self._track["f_normal"] = self.unit_vector_cross(self._track["hf_vector"], self._track["vf_vector"])

                # Difference in distance to center of face from the left and right iris, use to calculate vertical gaze vector
                self._track["left_iris_x_space"] = self._track["lm_133"].x - self._track["lm_468"].x
                self._track["right_iris_x_space"] = self._track["lm_362"].x - self._track["lm_473"].x
                self._track["eye_x_diff"] = (self._track["left_iris_x_space"] + self._track["right_iris_x_space"]) / 0.03
                self._track["eye_x_normal"] = self.rh_to_screenspace(self.theta_phi_to_unit_vector(self._track["eye_x_diff"] * -90, 90))

                # Get average height of eye tracking points, calculate the iris position compared to total height, keep track of average neutral eye position
                self._track["eye_y_total"] = (self._track["lm_230"].y + self._track["lm_450"].y - self._track["lm_27"].y - self._track["lm_257"].y) / 2
                self._track["eye_y_iris"] = (self._track["lm_230"].y + self._track["lm_450"].y - self._track["lm_468"].y - self._track["lm_473"].y) / 2
                self._track["eye_y_diff"] = self._track["eye_y_iris"] / self._track["eye_y_total"]
                self._track["y_running_average"] += (self._track["eye_y_diff"] - self._track["y_running_average"]) / self._frames

                # Calculate horizontal gaze vector based on iris y-diff compared to running y-average
                self._track["eye_y_normal"] = self.rh_to_screenspace(self.theta_phi_to_unit_vector(0, 90 + ((self._track["eye_y_diff"] - self._track["y_running_average"]) / 0.01)))
                
                # Calculate vector based on face-normal +/- average eye normals
                self._track["g_normal"] = tuple(i for i in (
                    (self._track["f_normal"][0] + self._track["eye_x_normal"][0]) / 2,
                    (self._track["f_normal"][1] + self._track["eye_y_normal"][1]) / 2,
                    (self._track["f_normal"][2] + self._track["eye_x_normal"][2] + self._track["eye_y_normal"][2]) / 3)
                )

    def close(self):
        """
        Stops the gaze tracking process.
        """
        self._active = False

    def _visualise(self):
        """
        Visualizes the gaze tracking results on the video feed.
        """
        h, w = self._frame.shape[:2]
        overlay = self._frame.copy()

        # Visualize
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_199"], w, h), self.lm_to_int_2d_add(self._track["lm_199"], self._track["vf_vector"], w, h), (255,255,0, 0.1), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_156"], w, h), self.lm_to_int_2d_add(self._track["lm_156"], self._track["hf_vector"], w, h), (255,255,0, 0.1), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_168"], w, h), self.lm_to_int_2d_add(self._track["lm_168"], self._track["f_normal"], w, h), (205,105,105, 0.1), 2, 1, 0)

        cv.circle(overlay, self.lm_to_int_2d(self._track["lm_468"], w, h), 2, (255,255,0, 0.1), 1, 1, 0)
        cv.circle(overlay, self.lm_to_int_2d(self._track["lm_473"], w, h), 2, (255,255,0, 0.1), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_468"], w, h), self.lm_to_int_2d_add(self._track["lm_468"], self._track["eye_x_normal"], w, h), (255,255,0, 0.1), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_473"], w, h), self.lm_to_int_2d_add(self._track["lm_473"], self._track["eye_x_normal"], w, h), (255,255,0, 0.1), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_468"], w, h), self.lm_to_int_2d_add(self._track["lm_468"], self._track["eye_y_normal"], w, h), (255,255,0, 0.1), 1, 1, 0)
        cv.line(overlay, self.lm_to_int_2d(self._track["lm_473"], w, h), self.lm_to_int_2d_add(self._track["lm_473"], self._track["eye_y_normal"], w, h), (255,255,0, 0.1), 1, 1, 0)

        result = cv.addWeighted(overlay, 0.3, self._frame, 1, 0)
        cv.line(result, self.lm_to_int_2d(self._track["lm_168"], w, h), self.lm_to_int_2d_add(self._track["lm_168"], self._track["g_normal"], w, h), (205,100,205, 0.1), 2, 1, 0)

        if (self._gazeaway):
            cv.putText(result, "GAZEAWAY DETECTED", (35, 35), cv.FONT_HERSHEY_DUPLEX, 1, (147, 58, 31), 2)
        else:
            cv.putText(result, "FOCUSING", (35, 35), cv.FONT_HERSHEY_DUPLEX, 1, (147, 58, 31), 2)
        cv.putText(result, f"XDIFF: {abs(self._track["g_normal"][0])}", (35, 65), cv.FONT_HERSHEY_DUPLEX, 0.75, (147, 58, 31), 2)
        cv.putText(result, f"YDIFF: {abs(self._track["g_normal"][1])}", (35, 95), cv.FONT_HERSHEY_DUPLEX, 0.75, (147, 58, 31), 2)
        
        cv.imshow("_feed", result)
    
    @staticmethod
    def theta_phi_to_unit_vector(theta, phi):
        """
        Converts spherical coordinates (theta, phi) to a unit vector.

        Args:
            theta (float): Horizontal angle in degrees.
            phi (float): Vertical angle in degrees.

        Returns:
            tuple: A unit vector (x, y, z).
        """
        return (np.sin(phi * np.pi / 180)*np.cos(theta * np.pi / 180), 
                np.sin(phi * np.pi / 180)*np.sin(theta * np.pi / 180), 
                np.cos(phi * np.pi / 180))

    @staticmethod
    def lm_to_int_2d_add(lm, v, w, h):
        """
        Converts a landmark to 2D integer coordinates with an offset.

        Args:
            lm (object): Landmark object with x and y attributes.
            v (tuple): Offset vector (x, y).
            w (int): Frame width.
            h (int): Frame height.

        Returns:
            tuple: 2D integer coordinates (x, y).
        """
        return (int((lm.x + v[0])*w), int((lm.y + v[1])*h))

    @staticmethod
    def lm_to_int_2d(lm, w, h):
        """
        Converts a landmark to 2D integer coordinates.

        Args:
            lm (object): Landmark object with x and y attributes.
            w (int): Frame width.
            h (int): Frame height.

        Returns:
            tuple: 2D integer coordinates (x, y).
        """
        return (int(lm.x*w), int(lm.y*h))
    
    @staticmethod
    def lm_vector_from_to(a, b):
        """
        Calculates the vector from one landmark to another.

        Args:
            a (object): Starting landmark with x, y, z attributes.
            b (object): Ending landmark with x, y, z attributes.

        Returns:
            list: Vector [dx, dy, dz].
        """
        return [b.x - a.x, b.y - a.y, b.z - a.z]

    @staticmethod
    def unit_vector_cross(v1, v2):
        """
        Calculates the unit vector of the cross product of two vectors.

        Args:
            v1 (list): First vector.
            v2 (list): Second vector.

        Returns:
            np.ndarray: Unit vector of the cross product.
        """
        normal = np.cross(v1, v2)
        return Gaze.set_vector_length(normal, 1)

    @staticmethod
    def rh_to_screenspace(v):
        """
        Convert a vector from right handed coordinate system to screen-space.

        Args:
            v (list): Vector to transform.

        Returns:
            tuple: Vector in screen space.
        """
        return (v[1],v[2],v[0])
    
    @staticmethod
    def set_vector_length(v, r):
        """
        Set a vector to specified norm in the same direction.

        Args:
            v (list): Vector to transform.
            r (int): New vector length

        Returns:
            v (list): Vector with the new length.
        """
        return v / np.linalg.norm(v) * r