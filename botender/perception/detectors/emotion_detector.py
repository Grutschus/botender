import logging
import pickle

from pandas import DataFrame
from pkg_resources import resource_filename
from sklearn.svm import SVC  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

SVM_MODEL_PATH = resource_filename(__name__, "models/svm_model.pkl")
SCALER_MODEL_PATH = resource_filename(__name__, "models/scaler.pkl")
LABEL_ENCODER_MODEL_PATH = resource_filename(__name__, "models/label_encoder.pkl")


class EmotionDetector:
    """The EmotionDetector is responsible for predict the emotion of the user."""

    _model: SVC  # or whatever model we use

    def __init__(self):
        # load model
        logger.info("Loading emotion detection model...")
        # Load the model from the file
        with open(SVM_MODEL_PATH, "rb") as file:
            self.loaded_model = pickle.load(file)

        with open(SCALER_MODEL_PATH, "rb") as file:
            self.loaded_scaler = pickle.load(file)

        with open(LABEL_ENCODER_MODEL_PATH, "rb") as file:
            self.loaded_label_encoder = pickle.load(file)

    def detect_emotion(self, features: DataFrame) -> str:
        """Predicts the emotion in the given features and returns it as a string."""

        if len(features) == 0:
            return "neutral"

        scaled_aus = self.loaded_scaler.transform(features[0])
        predictions = self.loaded_model.predict(scaled_aus)
        predicted_emotions = self.loaded_label_encoder.inverse_transform(predictions)

        return predicted_emotions[0]
