"""Startup file for botender."""

import argparse
import logging
import time
from multiprocessing import Process, Queue

import cv2  # type: ignore
from dotenv import load_dotenv

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
NUMBER_OF_CELLS_PER_SIDE: int = 7

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
    # Load environment variables
    load_dotenv()

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
        perception_manager,
        webcam_processor,
        furhat_remote_address,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        NUMBER_OF_CELLS_PER_SIDE,
    )
    interaction_thread.start()


def teardown():
    """Main teardown function."""
    logger.info("Stopping botender...")

    logger.debug("Stopping interaction thread...")
    interaction_thread.stopThread()
    interaction_thread.join()
    logger.debug("Interaction thread stopped.")

    global perception_manager
    logger.debug("Stopping perception manager...")
    perception_manager.shutdown()
    logger.debug("Perception manager stopped.")

    global webcam_processor
    logger.debug("Stopping webcam processor...")
    webcam_processor.shutdown()
    logger.debug("Webcam processor stopped.")

    logger.debug("Cleanup done. Shutting down logging engine and exiting...")
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
            start_time = time.monotonic()
            render()
            end_time = time.monotonic()

            # Limit FPS
            time.sleep(max(0, 1 / MAX_FPS - (end_time - start_time)))

            if (key := cv2.waitKey(1) & 0xFF) == ord("q"):
                run = False
            elif key == ord("f"):
                logger.info("Toggling rendering of face boxes and emotion...")
                webcam_processor.debug_flags[
                    "face_rectangles"
                ] = not webcam_processor.debug_flags["face_rectangles"]
                webcam_processor.debug_flags[
                    "emotion"
                ] = not webcam_processor.debug_flags["emotion"]
            elif key == ord("g"):
                logger.info("Toggling rendering of the grid...")
                webcam_processor.debug_flags["grid"] = not webcam_processor.debug_flags[
                    "grid"
                ]
            elif key == ord("d"):
                logger.info("Toggling debug screen...")
                webcam_processor.debug_flags[
                    "debug_info"
                ] = not webcam_processor.debug_flags["debug_info"]

    except KeyboardInterrupt:
        pass

    teardown()
