from pandas import DataFrame
from sklearn.svm import SVC  # type: ignore
import logging

logger = logging.getLogger(__name__)


class EmotionDetector:
    """The EmotionDetector is responsible for predict the emotion of the user."""

    _model: SVC  # or whatever model we use

    def __init__(self):
        # load model
        logger.info("Loading emotion detection model...")

    def detect_emotion(self, features: DataFrame) -> str:
        """Predicts the emotion in the given features and returns it as a string."""

        raise NotImplementedError
