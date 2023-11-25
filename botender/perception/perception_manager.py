import logging
from multiprocessing import Manager, Queue
from multiprocessing.managers import ListProxy
from multiprocessing.managers import SyncManager as ManagerType
from threading import Lock as LockType

from botender.perception.detection_worker import DetectionResult, DetectionWorker
from botender.webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)


class PerceptionManager:
    """The PerceptionManager class is responsible for spawning and managing the
    detection worker process and communicating results."""

    _stopped: bool = False
    _current_result: DetectionResult | None = None
    _mp_manager: ManagerType
    _frame_list: ListProxy
    _frame_list_lock: LockType
    _result_list: ListProxy
    _result_list_lock: LockType
    _child_process: DetectionWorker
    _webcam_processor: WebcamProcessor

    def __init__(self, logging_queue: Queue, webcam_processor: WebcamProcessor):
        logger.debug("Initializing PerceptionManager...")
        self._webcam_processor = webcam_processor

        # Initializing child workers
        self._mp_manager = Manager()
        self._frame_list = self._mp_manager.list()
        self._frame_list_lock = self._mp_manager.Lock()
        self._result_list = self._mp_manager.list()
        self._result_list_lock = self._mp_manager.Lock()
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

        logger.debug("Received stop signal. Stopping PerceptionManager...")

        logger.debug("Sending stop signal to detection worker...")
        self._frame_list_lock.acquire()
        self._frame_list[:] = [None]
        self._frame_list_lock.release()
        self._child_process.join(10)
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
