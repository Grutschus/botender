from feat import Detector  # type: ignore
from botender.webcam_processor import Rectangle

from pandas import DataFrame


class FacialExpressionDetector:
    """The FacialExpressionDetector is responsible for detecting faces and extracting
    features from them."""

    _detector: Detector
    _faces: list[tuple[float, float, float, float, float]]

    def __init__(self, device: str = "cpu"):
        self._detector = Detector(device=device)

    def detect_faces(self, frame) -> list[Rectangle]:
        """Detects faces in a frame and returns a list of rectangles representing the
        faces."""

        self._faces = self._detector.detect_faces(frame)[0]
        return [((x1, y1), (x2, y2)) for x1, y1, x2, y2, _ in self._faces]

    def extract_features(self) -> DataFrame:
        """Extracts features from the faces detected in the last frame and returns them
        as a DataFrame."""

        raise NotImplementedError
