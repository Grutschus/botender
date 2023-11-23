import logging
import random
import time
from threading import Thread


logger = logging.getLogger(__name__)


# define the FacialExpressionExtractor class
class FacialExpressionExtractor:
    def captureFacialExpression(self):
        aus = [1, 2, 4, 5, 6, 7, 9, 10, 12, 14, 15, 17, 20, 23, 25, 26]
        time.sleep(1)
        return aus


# define the EmotionDetector class
class EmotionDetector:
    def __init__(self):
        self.model = None
        # self.model = joblib.load("model.pkl")

    def detectEmotion(self, aus):
        emotion = random.choice(
            ["happy", "sad", "angry", "surprised", "disgusted", "fearful"]
        )
        time.sleep(1)
        return emotion


# define the PyfeatThread class
class PyfeatThread(Thread):
    stopped: bool = False
    emotion: str = ""
    facialExpressionExtractor: FacialExpressionExtractor
    emotionDetector: EmotionDetector

    def __init__(self):
        super(PyfeatThread, self).__init__()
        self.facialExpressionExtractor = FacialExpressionExtractor()
        self.emotionDetector = EmotionDetector()

    def stopThread(self):
        self.stopped = True

    def run(self):
        logger.info("Started...")
        while not self.stopped:
            time.sleep(random.randint(1, 5))
            aus = self.facialExpressionExtractor.captureFacialExpression()
            self.emotion = self.emotionDetector.detectEmotion(aus)
            logger.debug("Emotion detected: " + self.emotion)
            # TODO: Show emotion
        logger.info("Finished.")
