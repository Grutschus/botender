import logging
import random
import time
from threading import Thread

from pyfeat_thread import PyfeatThread


logger = logging.getLogger(__name__)


# define the InteractionThread class
class InteractionThread(Thread):
    def __init__(self, pyfeat_thread: PyfeatThread):
        super(InteractionThread, self).__init__()
        self.pyfeat_thread = pyfeat_thread

    def run(self):
        logger.info("Started...")
        while self.pyfeat_thread.emotion is None:
            time.sleep(1)
        for i in range(10):
            time.sleep(random.randint(1, 5))
            logger.debug("Current emotion: " + self.pyfeat_thread.emotion)
            # TODO: Show drink
        self.pyfeat_thread.stopThread()
        logger.info("Finished.")
