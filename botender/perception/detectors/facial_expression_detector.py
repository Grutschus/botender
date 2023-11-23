import time

from feat import Detector  # type: ignore
from botender.webcam_processor import Rectangle


class FacialExpressionDetector:
    detector: Detector

    def __init__(self):
        self.detector = Detector(device="mps")

    def detect_faces(self, frame) -> list[Rectangle]:
        faces = self.detector.detect_faces(frame)
        return [((x1, y1), (x2, y2)) for x1, y1, x2, y2, _ in faces[0]]

    def capture_facial_expression(self):
        aus = [1, 2, 4, 5, 6, 7, 9, 10, 12, 14, 15, 17, 20, 23, 25, 26]
        time.sleep(1)
        return aus
