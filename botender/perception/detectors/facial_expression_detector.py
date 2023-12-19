import numpy as np
from feat import Detector  # type: ignore
from typing import Tuple

from botender.webcam_processor import Rectangle


class FacialExpressionDetector:
    """The FacialExpressionDetector is responsible for detecting faces and extracting
    features from them."""

    _detector: Detector
    _faces: list[tuple[float, float, float, float, float]]
    _features: list

    def __init__(self, detector: Detector):
        self._detector = detector

    def detect_faces(self, frame) -> list[Rectangle]:
        """Detects faces in a frame and returns a list of rectangles representing the
        faces."""

        self._faces = self._detector.detect_faces(frame)[0]
        return [((x1, y1), (x2, y2)) for x1, y1, x2, y2, _ in self._faces]

    def extract_features(self, frame: np.ndarray) -> Tuple[list, list]:
        """Extracts features from the faces detected in the last frame and returns them
        as a list. Returns additionally a list of the faces that were used to extract."""

        faces = self._faces
        if len(faces) == 0:
            return ([], faces)

        landmarks = self._detector.detect_landmarks(frame, [faces])

        return (landmarks, faces)
