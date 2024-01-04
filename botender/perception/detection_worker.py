import logging
import warnings
from dataclasses import dataclass
from multiprocessing import Process, Queue
from multiprocessing.connection import Connection

import numpy as np
import torch
from feat import Detector  # type: ignore

import botender.logging_utils as logging_utils
from botender.perception.detectors import EmotionDetector, FacialExpressionDetector
from botender.webcam_processor import Rectangle

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

EMOTION_DETECTION_FRAME_COUNT = 60
"""The number of frames to use for emotion detection."""
EMOTION_DETECTION_FRAME_SKIP = 30
"""The number of frames to skip between emotion detections."""


@dataclass
class DetectionResult:
    faces: list[Rectangle]
    """A list of rectangles representing the faces detected in the frame."""
    features: list
    """A list containing all the features extracted from the frame."""
    emotion: str
    """A string that defines the detected emotion."""


class DetectionWorker(Process):
    """A worker process that detects faces and emotions in frames."""

    _logging_queue: Queue
    _result_connection: Connection
    _current_result: DetectionResult

    facial_expression_detector: FacialExpressionDetector
    emotion_detector: EmotionDetector
    work_frame: np.ndarray

    _last_emotions: list[str] = []
    _detect_emotion_counter: int = 0

    _detector: Detector

    def __init__(
        self,
        logging_queue: Queue,
        frame_shape: tuple[int, ...],
        shared_array,
        result_connection: Connection,
        stop_event,
        detect_emotion_event,
    ):
        super().__init__(name="DetectionWorkerProcess")
        logger.debug("Initializing detection worker...")
        self._logging_queue = logging_queue
        self.frame_shape = frame_shape
        self._shared_array = shared_array
        self._result_connection = result_connection
        self._stop_event = stop_event
        self._detect_emotion_event = detect_emotion_event
        self._current_result = DetectionResult(faces=[], features=[], emotion="neutral")

    def run(self):
        """Uses the detectors to detect faces and emotions in the newest frames."""

        logging_utils.configure_publisher(self._logging_queue)
        logger.debug("Successfully spawned detection worker. Initializing detector...")
        self._detector = Detector(device=_get_device())
        self.facial_expression_detector = FacialExpressionDetector(
            detector=self._detector
        )
        self.emotion_detector = EmotionDetector(detector=self._detector)
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
                self.work_frame = _work_frame.copy()
                _work_frame[:] = 0
            # No new work available
            if np.array_equal(
                self.work_frame, np.zeros(self.frame_shape, dtype=np.uint8)
            ):
                continue

            # Do the work
            faces = self.facial_expression_detector.detect_faces(self.work_frame)
            self._current_result.faces = faces

            clear_flag = False
            if self._detect_emotion_event.is_set():
                clear_flag = self.detect_emotion()

            # Send the result
            self._result_connection.send(self._current_result)
            if clear_flag:
                self._detect_emotion_event.clear()

    def detect_emotion(self) -> bool:
        """Detects the emotion of the user."""
        clear_flag = False

        if self._detect_emotion_counter % EMOTION_DETECTION_FRAME_SKIP != 0:
            self._detect_emotion_counter += 1
            return clear_flag

        # extract features
        features, faces = self.facial_expression_detector.extract_features(
            self.work_frame
        )
        self._current_result.features = features
        # predict emotion
        emotion = self.emotion_detector.detect_emotion(
            frame=self.work_frame, faces=faces, features=features
        )
        self._last_emotions.append(emotion)

        self._detect_emotion_counter += 1

        if self._detect_emotion_counter > EMOTION_DETECTION_FRAME_COUNT:
            # update emotion by majority vote
            self._current_result.emotion = max(
                set(self._last_emotions), key=self._last_emotions.count
            )
            # reset emotion detection attributes
            self._last_emotions = []
            self._detect_emotion_counter = 0
            clear_flag = True

        return clear_flag


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
