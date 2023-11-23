"""Startup file for botender."""

import argparse
import datetime
import logging
import os
import sys
from time import sleep

import colorlog
import cv2  # type: ignore
from interaction_thread import InteractionThread
from pyfeat_thread import PyfeatThread
from webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)
pyfeat_thread: PyfeatThread
interaction_thread: InteractionThread
webcam_processor: WebcamProcessor


def parse_args():
    parser = argparse.ArgumentParser(description="Botender")

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    return parser.parse_args()


def setup_logging(debug: bool) -> None:
    log_format_color = (
        "%(asctime)s - "
        "%(log_color)s%(levelname)s%(reset)s - "
        "%(module)s - %(message)s"
    )
    log_format = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
    log_colors_config = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
    }

    colorlog_formatter = colorlog.ColoredFormatter(
        log_format_color,
        datefmt="%Y-%m-%d %H:%M:%S",
        reset=True,
        log_colors=log_colors_config,
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(colorlog_formatter)

    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_filename = f"logs/botender-{timestamp}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    if debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)


def setup():
    """Main setup function."""
    logger.info("Starting botender...")

    # Webcam
    global webcam_processor
    webcam_processor = WebcamProcessor()

    # PyFeat
    global pyfeat_thread
    pyfeat_thread = PyfeatThread()
    pyfeat_thread.start()

    # Interaction
    global interaction_thread
    interaction_thread = InteractionThread(pyfeat_thread)
    interaction_thread.start()


def teardown():
    """Main teardown function."""
    logger.info("Stopping botender...")

    pyfeat_thread.stopThread()
    interaction_thread.stopThread()
    pyfeat_thread.join()
    interaction_thread.join()


def render():
    """Main render loop."""

    webcam_processor.capture()
    webcam_processor.render()


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.debug)

    setup()

    # Enter the render loop
    run = True
    try:
        while run:
            render()
            sleep(0.01)  # 100 FPS
            if cv2.waitKey(1) & 0xFF == ord("q"):
                run = False
    except KeyboardInterrupt:
        pass

    teardown()
