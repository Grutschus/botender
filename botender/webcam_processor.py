"""Class for capturing the webcam footage and rendering stuff to the screen."""

import logging
import threading
from functools import partial
from typing import Callable

import cv2  # type: ignore
import numpy as np

from botender.types import Rectangle


logger = logging.getLogger(__name__)

ModifierKeyType = int | str
FrameModifier = Callable[[np.ndarray], np.ndarray]


class WebcamProcessor:
    """Class for capturing the webcam footage and rendering information to the screen."""

    _current_frame: np.ndarray
    _camera: cv2.VideoCapture
    _window_name: str
    _modifier_lock: threading.Lock
    _modifier_dict: dict[ModifierKeyType, FrameModifier]
    _debug_info: dict[str, str]
    _debug_flags: dict[str, bool] = {"debug_info": False, "face_rectangles": False}
    _FRAME_WIDTH: int = 640
    _FRAME_HEIGHT: int = 480

    def __init__(
        self,
        window_name: str = "Botender",
        frame_width: int = 640,
        frame_height: int = 480,
    ):
        """Initialize the ImageProcessor class."""

        self._FRAME_WIDTH = frame_width
        self._FRAME_HEIGHT = frame_height

        self._camera = cv2.VideoCapture(0)
        self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, self._FRAME_WIDTH)
        self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self._FRAME_HEIGHT)

        # initialize the current frame to black
        self._current_frame = np.zeros(
            (self._FRAME_WIDTH, self._FRAME_HEIGHT, 3), np.uint8
        )

        # initialize the modifier lock
        self._modifier_lock = threading.Lock()
        self._modifier_dict = {}

        # initialize the debug info
        self._debug_info = {}

        self._window_name = window_name
        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self._window_name, self._FRAME_WIDTH, self._FRAME_HEIGHT)

    def shutdown(self):
        """Deinitialize the ImageProcessor class."""

        logger.debug("Deinitializing WebcamProcessor...")
        self._camera.release()
        cv2.destroyAllWindows()

    def capture(self) -> None:
        """Capture a frame from the webcam."""

        ret, current_frame = self._camera.read()
        if not ret:
            logger.warning("Failed to capture frame from webcam.")
            return
        self._current_frame = current_frame

    def render(self) -> None:
        """Render the frame to the screen."""

        render_frame = self._current_frame.copy()
        self._modifier_lock.acquire()

        # Remove all modifiers that are disabled
        filtered_modifier_dict = {
            key: func
            for key, func in self._modifier_dict.items()
            if self._debug_flags.get(str(key), True)
        }

        for modifier_func in filtered_modifier_dict.values():
            render_frame = modifier_func(render_frame)
        self._modifier_lock.release()

        cv2.imshow(self._window_name, render_frame)

    @property
    def current_frame(self) -> np.ndarray:
        """Return the current frame."""

        return self._current_frame

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

        self._modifier_dict[modifier_key] = modifier_func

        return modifier_key

    def remove_frame_modifier(self, modifier_key: ModifierKeyType | int) -> None:
        """Remove a frame modifier function."""

        self._modifier_lock.acquire()
        if modifier_key not in self._modifier_dict:
            logger.error(
                "Failed to remove frame modifier function. Key not found in modifier_dict."
            )
            return
        del self._modifier_dict[modifier_key]
        self._modifier_lock.release()

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

    def update_debug_info(self, key: str, value: str) -> None:
        """Update the debug info."""

        self._debug_info[key] = value
        self._add_debug_info_to_current_frame()

    def _add_debug_info_to_current_frame(
        self,
    ):
        """Add debug info to the current frame."""
        
        text = "\n".join(
            [
                f"{key}: {value}"
                for key, value in self._debug_info.items()
                if value is not None
            ]
        )
        modifier_func = partial(
            cv2.putText,
            text=text,
            org=(0, self._FRAME_HEIGHT - 10),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.5,
            color=(255, 0, 0),
            thickness=1,
        )

        self.add_frame_modifier(modifier_func, "debug_info")
