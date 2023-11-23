from threading import Thread
import time
import random
from webcam_thread import WebCamThread
import joblib

# define the FacialExpressionExtractor class
class FacialExpressionExtractor():
    def captureFacialExpression(self):
        aus = [1, 2, 4, 5, 6, 7, 9, 10, 12, 14, 15, 17, 20, 23, 25, 26]
        time.sleep(1)
        return aus

# define the EmotionDetector class
class EmotionDetector():
    def __init__(self):
        self.model = None
        # self.model = joblib.load("model.pkl")

    def detectEmotion(self, aus):
        emotion = random.choice(["happy", "sad", "angry", "surprised", "disgusted", "fearful"])
        time.sleep(1)
        return emotion

# define the PyfeatThread class
class PyfeatThread(Thread):
    def __init__(self, webcamThread: WebCamThread):
        super(PyfeatThread, self).__init__()
        self.emotion = None
        self.webCamThread = webcamThread
        self.stopThreadFlag = False
        self.facialExpressionExtractor = FacialExpressionExtractor()
        self.emotionDetector = EmotionDetector()

    def stopThread(self):
        self.stopThreadFlag = True

    def run(self):
        print("PyfeatThread - Started.")
        while not self.stopThreadFlag:
            time.sleep(random.randint(1, 5))
            aus = self.facialExpressionExtractor.captureFacialExpression()
            self.emotion = self.emotionDetector.detectEmotion(aus)
            print("PyfeatThread - Emotion detected: " + self.emotion)
            if self.webCamThread.is_alive():
                self.webCamThread.showEmotion(self.emotion)
        print("PyFeatThread - Finished.")