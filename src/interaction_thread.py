from threading import Thread
import time
import random
from pyfeat_thread import PyfeatThread
from webcam_thread import WebCamThread

# define the InteractionThread class
class InteractionThread(Thread):
    def __init__(self, pyfeat_thread: PyfeatThread, webcamThread: WebCamThread):
        super(InteractionThread, self).__init__()
        self.pyfeatThread = pyfeat_thread
        self.webCamThread = webcamThread

    def run(self):
        print("InteractionThread - Started.")
        while self.pyfeatThread.emotion is None:
            time.sleep(1)
        for i in range(10):
            time.sleep(random.randint(1, 5))
            print("InteractionThread - Current emotion: " + self.pyfeatThread.emotion)
            self.webCamThread.showMessage("Show drink!")
        self.pyfeatThread.stopThread()
        self.webCamThread.stopThread()
        print("InteractionThread - Finished.")