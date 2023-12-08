import datetime
import logging
import os
from logging import Filter
from logging.handlers import QueueHandler
from multiprocessing import Process, Queue

import colorlog

LOGGING_PROCESS: Process | None = None


class LogFilter(Filter):
    def filter(self, record):
        """Filter out useless pyfeat logs."""
        results = True
        if record.module == "detector":
            if record.funcName == "detect_faces" and record.levelno <= logging.WARNING:
                results = False
        return results


def _configure_listener(debug: bool):
    """Configure logging listener."""

    log_format_color = (
        "%(asctime)s - "
        "%(log_color)s%(levelname)s%(reset)s - "
        "%(module)s - %(message)s"
    )
    log_format = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"

    if debug:
        log_format_color = (
            "%(asctime)s - "
            "%(log_color)s%(levelname)s%(reset)s - "
            "%(module)s - %(funcName)s - %(message)s"
        )
        log_format = (
            "%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
        )

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

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(colorlog_formatter)

    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_filename = f"logs/botender-{timestamp}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addFilter(LogFilter())

    if debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)


def _listener_process(queue: Queue, debug: bool):
    """Logging listener process."""

    _configure_listener(debug=debug)
    while True:
        record = queue.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)


def configure_publisher(queue: Queue):
    """Configure a logging publisher process (like all workers)."""

    queue_handler = QueueHandler(queue)
    root_logger = logging.getLogger()
    root_logger.addHandler(queue_handler)
    root_logger.setLevel(logging.DEBUG)


def start_logging_process(debug: bool, queue: Queue) -> Process:
    """Setup logging process."""

    p = Process(target=_listener_process, args=(queue, debug), name="LoggingProcess")
    p.start()

    return p


def stop_logging_process(queue: Queue, process: Process):
    """Stop logging process."""
    queue.put_nowait(None)
    queue.close()
    queue.join_thread()
    process.join()
