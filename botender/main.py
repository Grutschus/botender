"""Startup file for botender."""

import argparse
import logging
from multiprocessing import Queue, Process
from time import sleep

import cv2  # type: ignore

import botender.logging_utils as logging_utils
from botender.interaction.interaction_manager import InteractionManagerThread
from botender.perception.perception_manager import PerceptionManager
from botender.webcam_processor import WebcamProcessor

perception_manager: PerceptionManager
interaction_thread: InteractionManagerThread
webcam_processor: WebcamProcessor

LOGGING_QUEUE: Queue = Queue()
LOGGING_PROCESS: Process | None = None
SCREEN_WIDTH: int = 640
SCREEN_HEIGHT: int = 480
MAX_FPS: int = 30

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Botender")

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    parser.add_argument(
        "--furhat_remote_address",
        type=str,
        help="The address of the Furhat remote server",
        default="localhost",
    )

    return parser.parse_args()


def setup(debug: bool = False, furhat_remote_address: str = "localhost"):
    """Main setup function."""
    # Logging
    global LOGGING_PROCESS
    LOGGING_PROCESS = logging_utils.start_logging_process(debug, LOGGING_QUEUE)
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
    interaction_thread = InteractionManagerThread(
        perception_manager, webcam_processor, furhat_remote_address
    )
    interaction_thread.start()


def teardown():
    """Main teardown function."""
    logger.info("Stopping botender...")

    interaction_thread.stopThread()
    interaction_thread.join()

    global perception_manager
    perception_manager.shutdown()

    global webcam_processor
    webcam_processor.shutdown()

    logger.debug("Stopping logging process...")
    global LOGGING_PROCESS
    logging_utils.stop_logging_process(LOGGING_QUEUE, LOGGING_PROCESS)


def render():
    """Main render loop."""
    webcam_processor.capture()
    perception_manager.run()
    webcam_processor.render()


if __name__ == "__main__":
    args = parse_args()

    setup(debug=args.debug, furhat_remote_address=args.furhat_remote_address)

    # Enter the render loop
    run = True
    try:
        while run:
            render()
            sleep(1 / MAX_FPS)
            if (key := cv2.waitKey(1) & 0xFF) == ord("q"):
                run = False
            elif key == ord("f"):
                logger.info("Toggling rendering of face boxes...")
                webcam_processor.debug_flags[
                    "face_rectangles"
                ] = not webcam_processor.debug_flags["face_rectangles"]
            elif key == ord("d"):
                logger.info("Toggling debug screen...")
                webcam_processor.debug_flags[
                    "debug_info"
                ] = not webcam_processor.debug_flags["debug_info"]

    except KeyboardInterrupt:
        pass

    teardown()