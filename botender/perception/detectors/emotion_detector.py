import logging

import numpy as np
from feat import Detector  # type: ignore
from feat.utils import FEAT_EMOTION_COLUMNS  # type: ignore

logger = logging.getLogger(__name__)

PYFEAT_EMOTIONS_TO_EMOTIONS = {
    "neutral": "neutral",
    "anger": "angry",
    "happiness": "happy",
    "sadness": "sad",
}


class EmotionDetector:
    """The EmotionDetector is responsible for predict the emotion of the user."""

    _detector: Detector  # use built-in pyfeat classifier

    def __init__(self, detector: Detector):
        self._detector = detector

    def detect_emotion(
        self,
        frame: np.ndarray,
        faces: list[tuple[float, float, float, float, float]],
        features: list,
    ) -> str:
        """Predicts the emotion in the given features and returns it as a string."""

        if len(faces) == 0 or len(features) == 0:
            return "neutral"

        detected_emotions = self._detector.detect_emotions(frame, [faces], features)[0]

        detected_emotion = FEAT_EMOTION_COLUMNS[np.argmax(detected_emotions[0])]
        if detected_emotion not in PYFEAT_EMOTIONS_TO_EMOTIONS.keys():
            detected_emotion = "neutral"
        predicted_emotion = PYFEAT_EMOTIONS_TO_EMOTIONS[detected_emotion]

        return predicted_emotion
