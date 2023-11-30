import logging
from dataclasses import dataclass
from multiprocessing import Process, Queue
from multiprocessing.connection import Connection
from queue import Empty as QueueEmptyException

import torch

import botender.logging_utils as logging_utils
from botender.perception.detectors import FacialExpressionDetector
from botender.types import Rectangle

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    faces: list[Rectangle]
    """A list of rectangles representing the faces detected in the frame."""


class DetectionWorker(Process):
    """A worker process that detects faces and emotions in frames."""

    _logging_queue: Queue
    _work_queue: Queue
    _result_connection: Connection

    def __init__(
        self,
        logging_queue: Queue,
        work_queue: Queue,
        result_connection: Connection,
    ):
        super().__init__()
        logger.debug("Initializing detection worker...")
        self._logging_queue = logging_queue
        self._work_queue = work_queue
        self._result_connection = result_connection

    def run(self):
        """Uses the detectors to detect faces and emotions in the newest frames."""

        logging_utils.configure_publisher(self._logging_queue)
        logger.debug("Successfully spawned detection worker. Initializing detector...")
        facial_expression_detector = FacialExpressionDetector(device=_get_device())
        # emotion_detector = EmotionDetector()
        logger.debug("Successfully initialized detector. Starting work loop...")
        self._result_connection.send(True)  # Signal that we are ready

        while True:
            # Wait for work
            work_frame = self._work_queue.get()

            # Empty the work queue
            try:
                frames_received = 1
                while True:
                    work_frame = self._work_queue.get(timeout=0.01)
                    if work_frame is None:  # Stop signal
                        break
                    frames_received += 1
            except QueueEmptyException:
                if frames_received > 1:
                    logger.debug(
                        f"Can't keep up! Dropped {frames_received - 1} frames."
                    )

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

            # Send the result
            self._result_connection.send(result)


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
