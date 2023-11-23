import logging
import time
from multiprocessing import Process, Queue
from multiprocessing.managers import ListProxy
from multiprocessing.synchronize import Lock as LockType
import botender.logging_utils as logging_utils
from botender.perception.detectors.facial_expression_detector import (
    FacialExpressionDetector,
)

logger = logging.getLogger(__name__)


class DetectionWorker(Process):
    def __init__(
        self,
        logging_queue: Queue,
        frame_list: ListProxy,
        result_list: ListProxy,
        frame_list_lock: LockType,
        result_list_lock: LockType,
    ):
        super().__init__()
        logger.debug("Initializing detection worker...")
        self.logging_queue = logging_queue
        self.frame_list = frame_list
        self.result_list = result_list
        self.frame_list_lock = frame_list_lock
        self.result_list_lock = result_list_lock

    def run(self):
        logging_utils.configure_publisher(self.logging_queue)
        logger.debug("Successfully spawned detection worker. Initializing detector...")
        facial_expression_detector = FacialExpressionDetector()
        logger.debug("Successfully initialized detector. Starting work loop...")

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
