import logging
import warnings
from dataclasses import dataclass
from multiprocessing import Process, Queue
from multiprocessing.connection import Connection

import numpy as np
import torch
from pandas import DataFrame

import botender.logging_utils as logging_utils
from botender.perception.detectors import EmotionDetector, FacialExpressionDetector
from botender.webcam_processor import Rectangle

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    faces: list[Rectangle]
    """A list of rectangles representing the faces detected in the frame."""
    features: DataFrame
    """A dataframe containing all the features extracted from the frame."""
    emotion: str
    """A string that defines the detected emotion."""


class DetectionWorker(Process):
    """A worker process that detects faces and emotions in frames."""

    _logging_queue: Queue
    _result_connection: Connection
    _current_result: DetectionResult

    def __init__(
        self,
        logging_queue: Queue,
        frame_shape: tuple[int, ...],
        shared_array,
        result_connection: Connection,
        stop_event,
        detect_emotion_event,
    ):
        super().__init__()
        logger.debug("Initializing detection worker...")
        self._logging_queue = logging_queue
        self.frame_shape = frame_shape
        self._shared_array = shared_array
        self._result_connection = result_connection
        self._stop_event = stop_event
        self._detect_emotion_event = detect_emotion_event
        self._current_result = DetectionResult(
            faces=[], features=DataFrame(), emotion="neutral"
        )

    def run(self):
        """Uses the detectors to detect faces and emotions in the newest frames."""

        logging_utils.configure_publisher(self._logging_queue)
        logger.debug("Successfully spawned detection worker. Initializing detector...")
        facial_expression_detector = FacialExpressionDetector(device=_get_device())
        emotion_detector = EmotionDetector()
        logger.debug("Successfully initialized detector. Starting work loop...")
        self._result_connection.send(True)  # Signal that we are ready

        while True:
            # React to stop signal
            if self._stop_event.is_set():
                logger.debug("Received stop signal. Exiting...")
                return

            # Get new frame
            with self._shared_array.get_lock():
                _work_frame = _to_numpy_array(self._shared_array, self.frame_shape)
                work_frame = _work_frame.copy()
                _work_frame[:] = 0
            # No new work available
            if np.array_equal(work_frame, np.zeros(self.frame_shape, dtype=np.uint8)):
                continue

            # Do the work
            faces = facial_expression_detector.detect_faces(work_frame)
            self._current_result.faces = faces

            if self._detect_emotion_event.is_set():
                # extract features
                features = facial_expression_detector.extract_features(work_frame)
                self._current_result.features = features
                # predict emotion
                emotion = emotion_detector.detect_emotion(features=features)
                self._current_result.emotion = emotion
                self._detect_emotion_event.clear()

            # Send the result
            self._result_connection.send(self._current_result)


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


def _to_numpy_array(shared_array, shape: tuple[int, ...] | None = None):
    """Converts a shared array to a numpy array."""
    if shape is None:
        return np.frombuffer(shared_array.get_obj(), dtype=np.uint8)
    else:
        return np.frombuffer(shared_array.get_obj(), dtype=np.uint8).reshape(shape)
