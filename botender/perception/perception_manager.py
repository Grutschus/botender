import logging
import multiprocessing
from multiprocessing import Queue

from botender.perception.detection_worker import DetectionResult, DetectionWorker
from botender.webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)


class PerceptionManager:
    """The PerceptionThread class is responsible for spawning and managing the
    detection worker process and communicating results."""

    _stopped: bool = False
    _current_result: DetectionResult | None = None
    _mp_manager: multiprocessing.Manager
    _frame_list: multiprocessing.list
    _frame_list_lock: multiprocessing.Lock
    _result_list: multiprocessing.list
    _result_list_lock: multiprocessing.Lock
    _child_process: DetectionWorker
    _webcam_processor: WebcamProcessor

    def __init__(self, logging_queue: Queue, webcam_processor: WebcamProcessor):
        logger.debug("Initializing PerceptionManager...")
        self._webcam_processor = webcam_processor

        # Initializing child workers
        self._mp_manager = multiprocessing.Manager()
        self._frame_list = self._mp_manager.list()
        self._frame_list_lock = multiprocessing.Lock()
        self._result_list = self._mp_manager.list()
        self._result_list_lock = multiprocessing.Lock()
        self._child_process = DetectionWorker(
            logging_queue,
            self._frame_list,
            self._result_list,
            self._frame_list_lock,
            self._result_list_lock,
        )
        logger.debug("Spawning child worker...")
        self._child_process.start()

    def shutdown(self):
        """Shutdowns the PerceptionManager and terminate its child worker."""
        
        logger.debug("Terminating child worker...")
        self._frame_list[:] = [None]
        self._child_process.join(1)
        if self._child_process.is_alive():
            logger.warning(
                "Child worker could not be terminated gracefully. Killing..."
            )
            self._child_process.terminate()

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

    def run(self) -> None:
        """Runs the PerceptionManager. Adds new work to the child worker and
        retrieves results."""

        # Add new work
        current_frame = self._webcam_processor.current_frame
        self._frame_list_lock.acquire()
        self._frame_list.append(current_frame)
        self._frame_list_lock.release()

        # Get results
        self._result_list_lock.acquire()
        if len(self._result_list) > 0:
            result: DetectionResult = self._result_list.pop()
            self._result_list[:] = []
            self._current_result = result  # No synchronization needed due to GIL
        self._result_list_lock.release()

        # Render results
        self._render_face_rectangles()

    def _render_face_rectangles(self) -> None:
        """Renders face rectangles to the current frame."""

        if self._current_result is None:
            return
        self._webcam_processor.add_rectangles_to_current_frame(
            self._current_result.faces, modifier_key="face_rectangles"
        )
