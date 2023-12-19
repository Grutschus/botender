import json
import logging
from pathlib import Path
from typing import Any, Literal, Union

import numpy as np
from pkg_resources import resource_filename

_GESTURE_PATH = resource_filename(__name__, "")
logger = logging.getLogger(__name__)

GestureType = Union[
    Literal["concern"],
    Literal["happy"],
    Literal["idle"],
    Literal["laugh"],
    Literal["listening"],
    Literal["thinking"],
    Literal["understand_issue"],
]


def get_random_gesture(gesture_type: GestureType) -> dict[str, Any]:
    """Returns a random gesture of the given type."""
    possible_gestures = _get_possible_gestures(gesture_type)
    if len(possible_gestures) == 0:
        logger.error(f"No gestures of type {gesture_type} found.")
        return {}
    rand_indx = np.random.randint(0, len(possible_gestures))
    selected_gesture = possible_gestures[rand_indx]
    logger.debug(f"Selected gesture {selected_gesture.stem}")
    with open(selected_gesture, "r") as file:
        return json.load(file)


def _get_possible_gestures(gesture_type: GestureType) -> list[Path]:
    """Returns a list of possible gestures of the given type."""
    gesture_path = Path(_GESTURE_PATH).joinpath(gesture_type)
    return list(gesture_path.glob("*.json"))
