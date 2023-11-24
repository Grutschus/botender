from pandas import DataFrame
from sklearn.svm import SVC  # type: ignore
import logging

logger = logging.getLogger(__name__)


class EmotionDetector:
    _model: SVC

    def __init__(self):
        # load model
        logger.info("Loading emotion detection model...")

    def detect_emotion(self, features: DataFrame) -> str:
        # predict emotion
        raise NotImplementedError
