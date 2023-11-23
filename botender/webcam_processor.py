"""Class for capturing the webcam footage and rendering stuff to the screen."""

import cv2  # type: ignore
import numpy as np
import logging
import threading
from typing import Callable
from functools import partial

ModifierKeyType = int | str

logger = logging.getLogger(__name__)

FrameModifier = Callable[[np.ndarray], np.ndarray]
Point = tuple[float, float]
"""Point is a tuple of two integers, x and y."""
Rectangle = tuple[Point, Point]
"""Rectangle is a tuple of two points, the lower left corner and the upper right corner."""


class WebcamProcessor:
    current_frame: np.ndarray
    camera: cv2.VideoCapture
    window_name: str
    modifier_lock: threading.Lock
    modifier_dict: dict[ModifierKeyType, FrameModifier]
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
        self.modifier_dict = {}

        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.FRAME_WIDTH, self.FRAME_HEIGHT)

    def __del__(self):
        """Deinitialize the ImageProcessor class."""
        logger.debug("Deinitializing WebcamProcessor...")
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
        render_frame = self.current_frame.copy()
        self.modifier_lock.acquire()
        for modifier_func in self.modifier_dict.values():
            render_frame = modifier_func(render_frame)
        self.modifier_lock.release()

        cv2.imshow(self.window_name, render_frame)

    def get_current_frame(self) -> np.ndarray:
        """Return the current frame."""
        return self.current_frame

    def add_frame_modifier(
        self,
        modifier_func: FrameModifier,
        modifier_key: ModifierKeyType | None = None,
    ) -> ModifierKeyType | int:
        """Add a frame modifier function.
        Pass a partial function that takes a frame as input and returns a frame as output."""
        # TODO validate the modifier_func

        if modifier_key is None:
            modifier_key = id(modifier_func)

        # Lock the modifiers list
        self.modifier_lock.acquire()
        self.modifier_dict[modifier_key] = modifier_func
        self.modifier_lock.release()

        return modifier_key

    def remove_frame_modifier(self, modifier_key: ModifierKeyType | int) -> None:
        """Remove a frame modifier function."""
        if modifier_key not in self.modifier_dict:
            logger.error(
                "Failed to remove frame modifier function. Key not found in modifier_dict."
            )
            return
        # Lock the modifiers list
        self.modifier_lock.acquire()
        del self.modifier_dict[modifier_key]
        self.modifier_lock.release()

    def add_text_to_current_frame(
        self,
        text: str,
        origin: tuple[int, int],
        color: tuple[int, int, int] = (255, 0, 0),
        modifier_key: ModifierKeyType | None = None,
    ) -> ModifierKeyType | int:
        """Add text to the current frame."""
        modifier_func = partial(
            cv2.putText,
            text=text,
            org=origin,
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=1,
            color=color,
            thickness=2,
        )

        return self.add_frame_modifier(modifier_func, modifier_key)

    def add_rectangle_to_current_frame(
        self,
        rectangle: Rectangle,
        color: tuple[int, int, int] = (255, 0, 0),
        modifier_key: ModifierKeyType | None = None,
    ) -> ModifierKeyType | int:
        """Add rectangle to the current frame."""
        modifier_func = partial(
            cv2.rectangle,
            pt1=(int(rectangle[0][0]), int(rectangle[0][1])),
            pt2=(int(rectangle[1][0]), int(rectangle[1][1])),
            color=color,
            thickness=2,
        )

        return self.add_frame_modifier(modifier_func, modifier_key)

    def add_rectangles_to_current_frame(
        self,
        rectangles: list[Rectangle],
        color: tuple[int, int, int] = (255, 0, 0),
        modifier_key: ModifierKeyType | None = None,
    ) -> ModifierKeyType | int:
        """Add rectangles to the current frame."""

        def modifier_func(frame: np.ndarray) -> np.ndarray:
            for rectangle in rectangles:
                frame = cv2.rectangle(
                    frame,
                    pt1=(int(rectangle[0][0]), int(rectangle[0][1])),
                    pt2=(int(rectangle[1][0]), int(rectangle[1][1])),
                    color=color,
                    thickness=2,
                )
            return frame

        return self.add_frame_modifier(modifier_func, modifier_key)
