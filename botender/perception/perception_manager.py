import logging
import multiprocessing as mp
from multiprocessing import Pipe, Queue
from multiprocessing.connection import Connection

import numpy as np

from botender.perception.detection_worker import DetectionResult, DetectionWorker
from botender.webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)


class PerceptionManager:
    """The PerceptionManager class is responsible for spawning and managing the
    detection worker process and communicating results."""

    _stopped: bool = False
    _current_result: DetectionResult | None = None
    _child_process: DetectionWorker
    _child_process_working: bool = False
    _webcam_processor: WebcamProcessor
    _result_pipe: tuple[Connection, Connection]
    _drop_counter: int = 0
    _face_presence_counter: int = 0

    def __init__(self, logging_queue: Queue, webcam_processor: WebcamProcessor):
        logger.debug("Initializing PerceptionManager...")
        self._webcam_processor = webcam_processor

        # Initializing child workers
        # Queue cannot fill up; Pipe buffer fills up and becomes blocking
        self.frame_shape = webcam_processor.current_frame.shape
        c_type = np.ctypeslib.as_ctypes_type(self._webcam_processor.current_frame.dtype)
        self._shared_array = mp.Array(c_type, int(np.prod(self.frame_shape)))
        self._stop_event = mp.Event()
        self._detect_emotion_event = mp.Event()
        self._result_pipe = Pipe(duplex=False)
        self._child_process = DetectionWorker(
            logging_queue,
            self.frame_shape,
            self._shared_array,
            self._result_pipe[1],  # conn2 can only send
            self._stop_event,
            self._detect_emotion_event,
        )
        logger.debug("Spawning child worker...")
        self._child_process.start()

    def shutdown(self):
        """Shutdowns the PerceptionManager and terminate its child worker."""

        logger.debug("Received stop signal. Stopping PerceptionManager...")

        logger.debug("Sending stop signal to detection worker...")
        self._stop_event.set()
        self._child_process.join(5)
        if self._child_process.is_alive():
            logger.warning(
                "Detection worker could not be terminated gracefully. Killing..."
            )
            self._child_process.terminate()
        else:  # Child process terminated gracefully
            logger.debug("Detection worker stopped.")

    @property
    def current_result(self) -> DetectionResult | None:
        """Returns the current detection result."""

        return self._current_result

    @current_result.setter
    def current_result(self, value: DetectionResult | None) -> None:
        logger.error("Setting _current_result is not allowed!")
        return

    @property
    def face_present(self) -> bool:
        """Returns True if a face is present in the current frame."""

        return self._current_result is not None and len(self._current_result.faces) > 0

    @property
    def face_presence_counter(self) -> int:
        """Returns the number of consecutive frames in which a face was present."""

        return self._face_presence_counter

    def detect_emotion(self) -> None:
        """Tells the PerceptionManager to detect emotions."""
        self._detect_emotion_event.set()

    def detects_emotion(self) -> bool:
        """Returns True if the PerceptionManager is currently detecting emotions."""
        return self._detect_emotion_event.is_set()

    def run(self) -> None:
        """Runs the PerceptionManager. Adds new work to the child worker and
        retrieves results."""

        result_connection = self._result_pipe[0]

        # Check if child process is ready to go
        if not self._child_process_working:
            if result_connection.poll():
                _ = result_connection.recv()
                logger.debug("Child process working. Received first result.")
                self._child_process_working = True
            else:
                return

        # Add new work
        current_frame = self._webcam_processor.current_frame
        with self._shared_array.get_lock():
            array = _to_numpy_array(self._shared_array, self.frame_shape)
            if not np.array_equal(array, np.zeros(self.frame_shape, dtype=np.uint8)):
                self._drop_counter += 1
            else:
                self._drop_counter = 0
            if self._drop_counter > 10:
                logger.debug(
                    f"Detection worker can't keep up! Dropped {self._drop_counter} frames."
                )

            array[:] = current_frame.copy()

        # Retrieve results
        if result_connection.poll():
            self._current_result = result_connection.recv()
            if self.face_present:
                self._face_presence_counter += 1
            else:
                self._face_presence_counter = 0

        # Render results
        self._render_face_rectangles()
        self._render_emotion()

    def _render_face_rectangles(self) -> None:
        """Renders face rectangles to the current frame."""

        if self._current_result is None:
            return
        self._webcam_processor.add_rectangles_to_current_frame(
            self._current_result.faces, modifier_key="face_rectangles"
        )

    def _render_emotion(self) -> None:
        """Renders the emotion to the current frame."""

        if self._current_result is None:
            return

        try:
            # pt1 = (x coord of bottom right corner, y coord of top left corner)
            # this is because the image is mirrored
            pt1 = (
                self._current_result.faces[0][1][0],
                self._current_result.faces[0][0][1],
            )
        except IndexError:
            return

        origin = (int(pt1[0]), int(pt1[1] - 10))
        self._webcam_processor.add_text_to_current_frame(
            self._current_result.emotion, origin=origin, modifier_key="emotion"
        )


def _to_numpy_array(shared_array, shape: tuple[int, ...] | None = None):
    """Converts a shared array to a numpy array."""
    if shape is None:
        return np.frombuffer(shared_array.get_obj(), dtype=np.uint8)
    else:
        return np.frombuffer(shared_array.get_obj(), dtype=np.uint8).reshape(shape)
