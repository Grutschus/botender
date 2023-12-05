import logging
from threading import Thread

from furhat_remote_api import FurhatRemoteAPI  # type: ignore

from botender.interaction.gaze_coordinator import GazeCoordinatorThread
from botender.interaction.gaze_coordinator import GazeClasses
from botender.interaction.interaction_coordinator import InteractionCoordinator
from botender.perception.perception_manager import PerceptionManager
from botender.webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)


# define the InteractionManagerThread class
class InteractionManagerThread(Thread):
    """The InteractionManagerThread is responsible for starting an interaction
    as soon as a face is detected.

    Currently, the interaction runs in the same thread, which means that the
    InteractionManager will start looking for new faces only after the
    interaction has finished.
    """

    _stopped: bool = False
    _perception_manager: PerceptionManager
    _webcam_processor: WebcamProcessor
    _gaze_coordinator: GazeCoordinatorThread
    _furhat: FurhatRemoteAPI
    _face_present_frame_counter: int = 0

    def __init__(
        self,
        perception_manager: PerceptionManager,
        webcam_processor: WebcamProcessor,
        furhat_remote_address: str,
        frame_width: int = 640,
        frame_height: int = 480,
        number_of_cells_per_side: int = 7,
    ):
        super(InteractionManagerThread, self).__init__()
        self._perception_manager = perception_manager
        self._webcam_processor = webcam_processor
        self._furhat = FurhatRemoteAPI(furhat_remote_address)
        self._gaze_coordinator = GazeCoordinatorThread(
            self._furhat, self._perception_manager, self._webcam_processor, frame_width, frame_height, number_of_cells_per_side
        )

        logger.debug("Spawning GazeCoordinatorThread...")
        self._gaze_coordinator.start()

    def stopThread(self):
        """Stops the Gazecoordinator and the InteractionManagerThread. Sets furhat to
        idle state."""

        logger.debug("Received stop signal. Stopping InteractionManagerThread...")
        self._stopped = True
        logger.debug("Sending stop signal to GazeCoordinatorThread...")
        self._gaze_coordinator.stopThread()
        self._gaze_coordinator.join()
        logger.debug("GazeCoordinatorThread stopped.")
        # TODO: set furhat to idle state

    def _start_interaction(self):
        """Create a new InteractionCoordinator and launch the interaction."""

        logger.info("Starting interaction...")
        interaction_coordinator = InteractionCoordinator(
            self._perception_manager, self._webcam_processor, self._furhat
        )
        interaction_coordinator.coordinate_interaction()

    def _should_start_interaction(self) -> bool:
        """Analyzes the output of the perception manager and checks if a new face
        has been detected and present for a given time."""

        if self._perception_manager.face_present:
            self._face_present_frame_counter += 1
        else:
            self._face_present_frame_counter = 0
        # A face has to be detected for at least 60 frames (2 seconds) before
        # starting an interaction
        return self._face_present_frame_counter > 60

    def run(self):
        """Starts the interaction as soon as a face is detected. Sets furhat to idle
        state when no face is detected."""

        logger.info("Started...")
        while not self._stopped:
            if self._should_start_interaction():
                self._gaze_coordinator.set_gaze_state(GazeClasses.FACE)
                self._start_interaction()
            else:
                self._gaze_coordinator.set_gaze_state(GazeClasses.IDLE)

            # else: randomly add whistles or other idle sounds and gestures
        logger.info("Received stop signal. Exiting...")
