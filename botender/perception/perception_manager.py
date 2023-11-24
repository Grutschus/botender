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

    def __init__(self, logging_queue: Queue, webcam_processor: WebcamProcessor):
        logger.debug("Initializing PerceptionManager...")
        self.webcam_processor = webcam_processor

        # Initializing child workers
        self.mp_manager = multiprocessing.Manager()
        self.frame_list = self.mp_manager.list()
        self.frame_list_lock = multiprocessing.Lock()
        self.result_list = self.mp_manager.list()
        self.result_list_lock = multiprocessing.Lock()
        self.child_process = DetectionWorker(
            logging_queue,
            self.frame_list,
            self.result_list,
            self.frame_list_lock,
            self.result_list_lock,
        )
        logger.debug("Spawning child worker...")
        self.child_process.start()

    def shutdown(self):
        logger.debug("Terminating child worker...")
        self.frame_list[:] = [None]
        self.child_process.join(1)
        if self.child_process.is_alive():
            logger.warning(
                "Child worker could not be terminated gracefully. Killing..."
            )
            self.child_process.terminate()

    @property
    def current_result(self) -> DetectionResult | None:
        return self._current_result

    @current_result.setter
    def current_result(self, value: DetectionResult | None) -> None:
        logger.error("Setting _current_result is not allowed!")
        return

    @property
    def face_present(self) -> bool:
        return self._current_result is not None and len(self._current_result.faces) > 0

    def run(self) -> None:
        # Maintaing the list of frames the child workers will process
        # Add new work
        current_frame = self.webcam_processor.current_frame
        self.frame_list_lock.acquire()
        self.frame_list.append(current_frame)
        self.frame_list_lock.release()

        # Get results
        self.result_list_lock.acquire()
        if len(self.result_list) > 0:
            result: DetectionResult = self.result_list.pop()
            self.result_list[:] = []
            self._current_result = result  # No synchronization needed due to GIL
        self.result_list_lock.release()

        # Render results
        self._render_face_rectangles()

    def _render_face_rectangles(self) -> None:
        if self._current_result is None:
            return
        self.webcam_processor.add_rectangles_to_current_frame(
            self._current_result.faces, modifier_key="face_rectangles"
        )
