import logging

from threading import Thread
from botender.webcam_processor import WebcamProcessor

from botender.perception.perception_manager import PerceptionManager


logger = logging.getLogger(__name__)


# define the InteractionThread class
class InteractionThread(Thread):
    stopped: bool = False
    pyfeat_thread: PerceptionManager
    webcam_processor: WebcamProcessor

    def __init__(
        self, pyfeat_thread: PerceptionManager, webcam_processor: WebcamProcessor
    ):
        super(InteractionThread, self).__init__()
        self.pyfeat_thread = pyfeat_thread
        self.webcam_processor = webcam_processor

    def stopThread(self):
        self.stopped = True

    def run(self):
        logger.info("Started...")
        # greeting_text = self.webcam_processor.add_text_to_current_frame(
        #     "Hello from InteractionThread!", (100, 100)
        # )
        while not self.stopped:
            pass
            # current_time = time.time()
            # self.webcam_processor.add_text_to_current_frame(
            #     "Time: " + str(current_time), (100, 100), modifier_key=greeting_text
            # )

        logger.info("Finished.")
