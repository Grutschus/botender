"""Startup file for botender."""

import argparse
import datetime
import logging
import os
import sys

import colorlog

logger = logging.getLogger(__name__)


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


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.debug)

    logger.info("Starting botender...")
