import logging
import time
from dataclasses import dataclass
from multiprocessing import Process, Queue
from multiprocessing.managers import ListProxy
from threading import Lock as LockType

import torch

import botender.logging_utils as logging_utils
from botender.perception.detectors import FacialExpressionDetector

# from botender.perception.detectors import EmotionDetector
from botender.types import Rectangle

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    faces: list[Rectangle]
    """A list of rectangles representing the faces detected in the frame."""


class DetectionWorker(Process):
    """A worker process that detects faces and emotions in frames."""

    _logging_queue: Queue
    _frame_list: ListProxy
    _result_list: ListProxy
    _frame_list_lock: LockType
    _result_list_lock: LockType

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
        self._logging_queue = logging_queue
        self._frame_list = frame_list
        self._result_list = result_list
        self._frame_list_lock = frame_list_lock
        self._result_list_lock = result_list_lock

    def run(self):
        """Uses the detectors to detect faces and emotions in the newest frames."""

        logging_utils.configure_publisher(self._logging_queue)
        logger.debug("Successfully spawned detection worker. Initializing detector...")
        facial_expression_detector = FacialExpressionDetector(device=_get_device())
        # emotion_detector = EmotionDetector()
        logger.debug("Successfully initialized detector. Starting work loop...")

        # Fresh start
        self._frame_list[:] = []
        while True:
            # Get work
            self._frame_list_lock.acquire()
            if len(self._frame_list) == 0:
                # No frame is available
                self._frame_list_lock.release()
                time.sleep(0.01)
                continue
            # Get the newest frame
            work_frame = self._frame_list.pop()
            # Drop all older frames
            if len(self._frame_list) > 0:
                logger.warning(
                    f"Can't keep up! Dropping {len(self._frame_list)} frames."
                )
                self._frame_list[:] = []
            self._frame_list_lock.release()

            # React to stop signal
            if work_frame is None:
                logger.debug("Received stop signal. Exiting...")
                return

            # Do the work
            faces = facial_expression_detector.detect_faces(work_frame)

            # TODO: extract features
            # TODO: predict emotion

            # Create result
            result = DetectionResult(faces=faces)

            # Add result
            self._result_list_lock.acquire()
            self._result_list.append(result)
            self._result_list_lock.release()


def _get_device():
    """Get the device to use for detection."""

    if torch.backends.cudnn.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    logger.info(f"Using device: {device}")
    return device
