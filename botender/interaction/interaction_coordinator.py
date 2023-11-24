import logging
import time

from botender.webcam_processor import WebcamProcessor

from botender.perception.perception_manager import PerceptionManager

from furhat_remote_api import FurhatRemoteAPI  # type: ignore


logger = logging.getLogger(__name__)


class InteractionCoordinator:
    """The InteractionCoordinator is responsible for coordinating the interaction and starting
    gaze coordination thread."""

    _perception_manager: PerceptionManager
    _webcam_processor: WebcamProcessor
    _furhat: FurhatRemoteAPI

    def __init__(
        self,
        perception_manager: PerceptionManager,
        webcam_processor: WebcamProcessor,
        furhat: FurhatRemoteAPI,
    ):
        self._perception_manager = perception_manager
        self._webcam_processor = webcam_processor
        self._furhat = furhat

    def coordinate_interaction(self):
        """Coordinates the basic interaction between furhat and the user. This includes
        starting the gaze coordination thread."""
        logger.info("Starting to coordinate an interaction.")
        time.sleep(50)
