import logging
from multiprocessing import Queue
from multiprocessing.connection import Connection
from queue import Full as QueueFullException
from multiprocessing import Pipe


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
    _work_queue: Queue

    def __init__(self, logging_queue: Queue, webcam_processor: WebcamProcessor):
        logger.debug("Initializing PerceptionManager...")
        self._webcam_processor = webcam_processor

        # Initializing child workers
        # Queue cannot fill up; Pipe buffer fills up and becomes blocking
        self._work_queue = Queue()
        self._result_pipe = Pipe(duplex=False)
        self._child_process = DetectionWorker(
            logging_queue,
            self._work_queue,
            self._result_pipe[1],  # conn2 can only send
        )
        logger.debug("Spawning child worker...")
        self._child_process.start()

    def shutdown(self):
        """Shutdowns the PerceptionManager and terminate its child worker."""

        logger.debug("Received stop signal. Stopping PerceptionManager...")

        logger.debug("Sending stop signal to detection worker...")
        self._work_queue.put(None)
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
        if current_frame is not None:
            try:
                self._work_queue.put(current_frame, block=False)
            except QueueFullException:
                logger.warning("Failed to add work to queue. Dropping frames...")
        else:
            logger.warning("No frame available, not sending work.")

        # Retrieve results
        if result_connection.poll():
            self._current_result = result_connection.recv()

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
