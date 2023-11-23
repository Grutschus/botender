import logging

from threading import Thread
from botender.webcam_processor import WebcamProcessor

from botender.perception.perception_manager import PerceptionManager


logger = logging.getLogger(__name__)


# define the InteractionThread class
class InteractionThread(Thread):
    stopped: bool = False
    perception_manager: PerceptionManager
    webcam_processor: WebcamProcessor

    def __init__(
        self, perception_manager: PerceptionManager, webcam_processor: WebcamProcessor
    ):
        super(InteractionThread, self).__init__()
        self.perception_manager = perception_manager
        self.webcam_processor = webcam_processor

    def stopThread(self):
        logger.debug("Stopping InteractionThread...")
        self.stopped = True

    def run(self):
        logger.info("Started...")
        while not self.stopped:
            pass

        logger.info("Finished.")
