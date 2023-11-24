from feat import Detector  # type: ignore
from botender.webcam_processor import Rectangle

from pandas import DataFrame


class FacialExpressionDetector:
    _detector: Detector
    _faces: list[tuple[float, float, float, float, float]]

    def __init__(self, device: str = "cpu"):
        self._detector = Detector(device=device)

    def detect_faces(self, frame) -> list[Rectangle]:
        self._faces = self._detector.detect_faces(frame)[0]
        return [((x1, y1), (x2, y2)) for x1, y1, x2, y2, _ in self._faces]

    def extract_features(self) -> DataFrame:
        raise NotImplementedError
