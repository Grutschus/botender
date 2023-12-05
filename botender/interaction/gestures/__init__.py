import json
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from pkg_resources import resource_filename

_GESTURE_PATH = resource_filename(__name__, "")


class GestureType(Enum):
    CONCERN = "concern"
    HAPPY = "happy"
    IDLE = "idle"
    LAUGH = "laugh"
    LISTENING = "listening"
    THINKING = "thinking"
    UNDERSTAND_ISSUE = "understand_issue"


def get_random_gesture(gesture_type: GestureType) -> dict[str, Any]:
    """Returns a random gesture of the given type."""
    possible_gestures = _get_possible_gestures(gesture_type)
    rand_indx = np.random.randint(0, len(possible_gestures))
    selected_gesture = possible_gestures[rand_indx]
    with open(selected_gesture, "r") as file:
        return json.load(file)


def _get_possible_gestures(gesture_type: GestureType) -> list[Path]:
    """Returns a list of possible gestures of the given type."""
    gesture_path = Path(_GESTURE_PATH).joinpath(gesture_type.value)
    return list(gesture_path.glob("*.json"))
