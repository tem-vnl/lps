import pytest
import numpy as np
from proctoring.gaze import Gaze

class MOCK_LM:
    x = None
    y = None
    z = None
    visibility = None
    prescence = None

    def __init__(self, x, y, z, vis, pres):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = vis
        self.prescence = pres

class TestData:
    THETA_PHI_PARIS = [(180, 90), (0, 0), (0, 180), (45, 45)]
    UNIT_VECTOR_PAIRS = [(-1, 0, 0), (0, 0, 1), (0, 0, -1), (1/2, 1/2, np.sqrt(1/2))]
    MOCK_LMS = [MOCK_LM(0.3, 0.5, -0.2, 0.0, 0.0), MOCK_LM(0.6, 0.17, -0.8, 0.0, 0.0)]
    OFFSETS = [(0.3, 0.2), (0.5, 0.1)]
    SCREEN_WIDTH = 150
    SCREEN_HEIGHT = 250

@pytest.fixture
def gaze():
    """
    Create a Gaze instance without running the constructor.
    """
    gaze = Gaze.__new__(Gaze)
        
    yield gaze

def test_spherical_to_cartesian(gaze):
    for i, (theta, phi) in enumerate(TestData.THETA_PHI_PARIS):
        np.testing.assert_almost_equal(gaze.theta_phi_to_unit_vector(theta, phi), TestData.UNIT_VECTOR_PAIRS[i])


def test_landmark_to_screen_point_with_offset(gaze):
    w, h = TestData.SCREEN_WIDTH, TestData.SCREEN_HEIGHT
    for lm in TestData.MOCK_LMS:
        for off in TestData.OFFSETS:
            assert gaze.lm_to_int_2d_add(lm, off, w, h) == (int((lm.x + off[0]) * w), int((lm.y + off[1]) * h))


def test_landmark_to_screen_point(gaze):
    w, h = TestData.SCREEN_WIDTH, TestData.SCREEN_HEIGHT
    for lm in TestData.MOCK_LMS:
        assert gaze.lm_to_int_2d(lm, w, h) == (int(lm.x * w), int(lm.y * h))

def test_landmarks_to_vector(gaze):
    lms = TestData.MOCK_LMS
    result_vector = (lms[1].x - lms[0].x, lms[1].y - lms[0].y, lms[1].z - lms[0].z)
    np.testing.assert_almost_equal(gaze.lm_vector_from_to(TestData.MOCK_LMS[0], TestData.MOCK_LMS[1]), result_vector)

def test_normal_vector_from_two_vectors(gaze):
    lms = TestData.MOCK_LMS
    v1 = (lms[0].x, lms[0].y, lms[0].z)
    v2 = (lms[1].x, lms[1].y, lms[1].z)
    normal = np.cross(v1, v2) / np.linalg.norm(np.cross(v1, v2))
    np.testing.assert_almost_equal(gaze.unit_vector_cross(v1, v2), normal)