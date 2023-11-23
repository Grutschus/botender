import logging
import multiprocessing
from botender.perception.detection_worker import DetectionWorker
from botender.webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)


class PerceptionManager:
    """The PerceptionThread class is responsible for spawning and managing the
    detection worker process and communicating results."""

    stopped: bool = False
    emotion: str = ""

    def __init__(self, webcam_processor: WebcamProcessor):
        logger.debug("Initializing PyfeatThread...")
        self.webcam_processor = webcam_processor

        # Initializing child workers
        self.mp_manager = multiprocessing.Manager()
        self.frame_list = self.mp_manager.list()
        self.frame_list_lock = multiprocessing.Lock()
        self.result_list = self.mp_manager.list()
        self.result_list_lock = multiprocessing.Lock()
        self.child_process = DetectionWorker(
            self.frame_list,
            self.result_list,
            self.frame_list_lock,
            self.result_list_lock,
        )
        logger.debug("Spawning child worker...")
        self.child_process.start()

    def __del__(self):
        self.child_process.terminate()

    def run(self):
        # Maintaing the list of frames the child workers will process
        # Add new work
        current_frame = self.webcam_processor.get_current_frame()
        self.frame_list_lock.acquire()
        # Prevent backlog of frames
        if len(self.frame_list) > 0:
            self.frame_list[:] = []  # ListProxy does not support clear()
        self.frame_list.append(current_frame)
        self.frame_list_lock.release()

        # Get results
        self.result_list_lock.acquire()
        if len(self.result_list) > 0:
            results = self.result_list.pop()
            self.result_list[:] = []
            # TODO Define a dataclass for these results
            self.webcam_processor.add_rectangles_to_current_frame(
                results, modifier_key="faces"
            )
        self.result_list_lock.release()
