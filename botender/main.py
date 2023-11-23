"""Startup file for botender."""

import argparse
import logging
from multiprocessing import Queue
from time import sleep

import cv2  # type: ignore

import botender.logging_utils as logging_utils
from botender.perception.perception_manager import PerceptionManager
from botender.webcam_processor import WebcamProcessor
from botender.interaction.interaction_coordinator import InteractionThread

perception_manager: PerceptionManager
interaction_thread: InteractionThread
webcam_processor: WebcamProcessor

LOGGING_QUEUE: Queue = Queue()
SCREEN_WIDTH: int = 640
SCREEN_HEIGHT: int = 480

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Botender")

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    return parser.parse_args()


def setup(debug: bool = False):
    """Main setup function."""
    # Logging
    logging_utils.start_logging_process(debug, LOGGING_QUEUE)
    logging_utils.configure_publisher(LOGGING_QUEUE)

    logger.info("Starting botender...")

    # Webcam
    global webcam_processor
    webcam_processor = WebcamProcessor(
        frame_height=SCREEN_HEIGHT, frame_width=SCREEN_WIDTH
    )

    # PyFeat
    global perception_manager
    perception_manager = PerceptionManager(
        logging_queue=LOGGING_QUEUE, webcam_processor=webcam_processor
    )

    # Interaction
    global interaction_thread
    interaction_thread = InteractionThread(perception_manager, webcam_processor)
    interaction_thread.start()


def teardown():
    """Main teardown function."""
    logger.info("Stopping botender...")

    global perception_manager
    perception_manager.shutdown()

    global webcam_processor
    webcam_processor.shutdown()

    interaction_thread.stopThread()
    interaction_thread.join()

    logger.debug("Stopping logging process...")
    logging_utils.stop_logging_process(LOGGING_QUEUE)


def render():
    """Main render loop."""

    webcam_processor.capture()
    perception_manager.run()
    webcam_processor.render()


if __name__ == "__main__":
    args = parse_args()

    setup(debug=args.debug)

    # Enter the render loop
    run = True
    try:
        while run:
            render()
            sleep(0.01)  # 100 FPS
            if (key := cv2.waitKey(1) & 0xFF) == ord("q"):
                run = False
            elif key == ord("f"):
                logger.info("Toggling rendering of face boxes...")
                perception_manager.flag_show_face_rectangles = (
                    not perception_manager.flag_show_face_rectangles
                )

    except KeyboardInterrupt:
        pass

    teardown()
