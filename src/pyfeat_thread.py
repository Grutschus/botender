import logging
import random
import time
from threading import Thread
from feat import Detector  # type: ignore
from webcam_processor import WebcamProcessor
from webcam_processor import Rectangle

logger = logging.getLogger(__name__)


# define the FacialExpressionExtractor class
class FacialExpressionExtractor:
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


# define the EmotionDetector class
class EmotionDetector:
    def __init__(self):
        self.model = None
        # self.model = joblib.load("model.pkl")

    def detect_emotion(self, aus):
        emotion = random.choice(
            ["happy", "sad", "angry", "surprised", "disgusted", "fearful"]
        )
        time.sleep(1)
        return emotion


# define the PyfeatThread class
class PyfeatThread(Thread):
    stopped: bool = False
    emotion: str = ""
    facial_expression_extractor: FacialExpressionExtractor
    emotion_detector: EmotionDetector

    def __init__(self, webcam_processor: WebcamProcessor):
        super(PyfeatThread, self).__init__()
        self.facial_expression_extractor = FacialExpressionExtractor()
        self.emotion_detector = EmotionDetector()
        self.webcam_processor = webcam_processor

    def stopThread(self):
        self.stopped = True

    def run(self):
        logger.info("Started...")
        # emotion_text = self.webcam_processor.add_text_to_current_frame(
        #     "Hello from PyfeatThread!", (200, 200)
        # )
        while not self.stopped:
            # self.webcam_processor.add_text_to_current_frame(
            #     "Emotion detected: " + self.emotion,
            #     (200, 200),
            #     modifier_key=emotion_text,
            # )

            # Detect the face
            frame = self.webcam_processor.get_current_frame()
            faces = self.facial_expression_extractor.detect_faces(frame)
            self.webcam_processor.add_rectangles_to_current_frame(
                faces, modifier_key="face_bboxes"
            )

        logger.info("Finished.")
