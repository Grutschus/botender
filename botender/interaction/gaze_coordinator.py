import logging
from enum import Enum
from threading import Thread

from furhat_remote_api import FurhatRemoteAPI  # type: ignore

from botender.perception.perception_manager import PerceptionManager
from botender.webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)


class GazeClasses(Enum):
    """The GazeClasses enum represents the different gaze classes that can be used
    to coordinate the gaze of the robot.
    """

    NONE = 0
    """The robot should look down."""

    FACE = 1
    """The robot should look at the face of the user."""

    IDLE = 2
    """The robot should look around."""


class GazeCoordinatorThread(Thread):
    """The GazeCoordinatorThread is responsible for coordinating the gaze of the robot.
    It is linked to an InteractionCoordinator and receives the gaze commands from it.
    """

    _furhat: FurhatRemoteAPI
    _perception_manager: PerceptionManager
    _webcam_processor: WebcamProcessor
    _stopped: bool = False
    _state: GazeClasses = GazeClasses.NONE

    def __init__(
        self,
        furhat: FurhatRemoteAPI,
        perception_manager: PerceptionManager,
        webcam_processor: WebcamProcessor,
    ):
        super(GazeCoordinatorThread, self).__init__()
        self._furhat = furhat
        self._perception_manager = perception_manager
        self._webcam_processor = webcam_processor

    def stopThread(self):
        logger.debug("Stopping GazeCoordinatorThread...")
        self._stopped = True

    def run(self):
        while not self._stopped:
            # Render the gaze state to the screen
            self._webcam_processor.update_debug_info("Gaze State", self._state)
            pass

    def set_gaze_state(self, state: GazeClasses):
        """Sets the gaze state of the robot."""
        if self._state != state:
            self._state = state
            logger.info(f"Setting gaze state to {state}")
