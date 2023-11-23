"""Class for capturing the webcam footage and rendering stuff to the screen."""

import cv2  # type: ignore
import numpy as np
import logging
import threading
from typing import Callable
from functools import partial

logger = logging.getLogger(__name__)

FrameModifier = Callable[[np.ndarray], np.ndarray]


class WebcamProcessor:
    current_frame: np.ndarray
    camera: cv2.VideoCapture
    window_name: str
    modifier_lock: threading.Lock
    modifier_list: list[FrameModifier]
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480

    def __init__(
        self,
        window_name: str = "Botender",
        frame_width: int = 640,
        frame_height: int = 480,
    ):
        """Initialize the ImageProcessor class."""
        self.FRAME_WIDTH = frame_width
        self.FRAME_HEIGHT = frame_height

        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)

        # initialize the current frame to black
        self.current_frame = np.zeros(
            (self.FRAME_WIDTH, self.FRAME_HEIGHT, 3), np.uint8
        )

        # initialize the modifier lock
        self.modifier_lock = threading.Lock()
        self.modifier_list = []

        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.FRAME_WIDTH, self.FRAME_HEIGHT)

    def __del__(self):
        """Deinitialize the ImageProcessor class."""
        self.camera.release()
        cv2.destroyAllWindows()

    def capture(self) -> None:
        """Capture a frame from the webcam."""
        ret, current_frame = self.camera.read()
        if not ret:
            logger.warning("Failed to capture frame from webcam.")
            return
        self.current_frame = current_frame

    def render(self) -> None:
        """Render the frame to the screen."""

        self.modifier_lock.acquire()
        for modifier_func in self.modifier_list:
            self.current_frame = modifier_func(self.current_frame)
        self.modifier_lock.release()

        cv2.imshow(self.window_name, self.current_frame)

    def get_current_frame(self) -> np.ndarray:
        """Return the current frame."""
        return self.current_frame

    def add_frame_modifier(self, modifier_func: FrameModifier) -> None:
        """Add a frame modifier function.
        Pass a partial function that takes a frame as input and returns a frame as output."""
        # TODO validate the modifier_func

        # Lock the modifiers list
        self.modifier_lock.acquire()
        self.modifier_list.append(modifier_func)
        self.modifier_lock.release()

    def add_text_to_current_frame(
        self, text: str, x: int, y: int, color: tuple[int, int, int] = (255, 0, 0)
    ) -> None:
        """Add text to the current frame."""
        modifier_func = partial(
            cv2.putText,
            text=text,
            org=(x, y),
            font=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=1,
            color=color,
            thickness=2,
        )

        self.add_frame_modifier(modifier_func)
