import logging
import multiprocessing
from multiprocessing import Queue

from botender.perception.detection_worker import DetectionResult, DetectionWorker
from botender.webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)


class PerceptionManager:
    """The PerceptionThread class is responsible for spawning and managing the
    detection worker process and communicating results."""

    stopped: bool = False
    current_result: DetectionResult | None = None

    def __init__(self, logging_queue: Queue, webcam_processor: WebcamProcessor):
        logger.debug("Initializing PerceptionManager...")
        self.webcam_processor = webcam_processor

        # Debug flags
        self._flag_show_face_rectangles = False

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
    def flag_show_face_rectangles(self) -> bool:
        return self._flag_show_face_rectangles

    @flag_show_face_rectangles.setter
    def flag_show_face_rectangles(self, value: bool) -> None:
        # switching off
        if not value and self._flag_show_face_rectangles:
            self.webcam_processor.remove_frame_modifier(modifier_key="face_rectangles")
        self._flag_show_face_rectangles = value

    def run(self) -> None:
        # Maintaing the list of frames the child workers will process
        # Add new work
        current_frame = self.webcam_processor.get_current_frame()
        self.frame_list_lock.acquire()
        self.frame_list.append(current_frame)
        self.frame_list_lock.release()

        # Get results
        self.result_list_lock.acquire()
        if len(self.result_list) > 0:
            result: DetectionResult = self.result_list.pop()
            self.result_list[:] = []
            self.current_result = result  # No synchronization needed due to GIL
        self.result_list_lock.release()

        # Render results
        self.render_face_rectangles()

    def render_face_rectangles(self) -> None:
        if self.current_result is None:
            return
        if self.flag_show_face_rectangles:
            self.webcam_processor.add_rectangles_to_current_frame(
                self.current_result.faces, modifier_key="face_rectangles"
            )
