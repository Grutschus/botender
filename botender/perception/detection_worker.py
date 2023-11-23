from multiprocessing import Process
import logging
import time
from botender.perception.detectors.facial_expression_detector import (
    FacialExpressionDetector,
)

logger = logging.getLogger(__name__)


class DetectionWorker(Process):
    def __init__(self, frame_list, result_list, frame_list_lock, result_list_lock):
        super().__init__()

        logger.debug("Initializing...")
        self.frame_list = frame_list
        self.result_list = result_list
        self.frame_list_lock = frame_list_lock
        self.result_list_lock = result_list_lock

    def run(self):
        logger.debug("Starting to work...")
        facial_expression_detector = FacialExpressionDetector()

        while True:
            self.frame_list_lock.acquire()
            if len(self.frame_list) == 0:
                time.sleep(0.01)
                self.frame_list_lock.release()
                continue

            work_frame = self.frame_list.pop()
            self.frame_list_lock.release()

            # Do the work
            faces = facial_expression_detector.detect_faces(work_frame)

            self.result_list_lock.acquire()
            self.result_list.append(faces)
            self.result_list_lock.release()
