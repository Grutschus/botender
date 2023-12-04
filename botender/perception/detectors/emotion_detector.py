from pandas import DataFrame
from sklearn.svm import SVC  # type: ignore
from sklearn.preprocessing import LabelEncoder, StandardScaler
import logging
import pickle

logger = logging.getLogger(__name__)


class EmotionDetector:
    """The EmotionDetector is responsible for predict the emotion of the user."""

    _model: SVC  # or whatever model we use

    def __init__(self):
        # load model
        logger.info("Loading emotion detection model...")
        # Load the model from the file
        with open('botender\perception\detectors\models\svm_model.pkl', 'rb') as file:
            self.loaded_model = pickle.load(file)

        with open('botender\perception\detectors\models\scaler.pkl', 'rb') as file:
            self.loaded_scaler = pickle.load(file)

        with open('botender\perception\detectors\models\label_encoder.pkl', 'rb') as file:
            self.loaded_label_encoder = pickle.load(file)

    def detect_emotion(self, features: DataFrame) -> str:
        """Predicts the emotion in the given features and returns it as a string."""
        scaled_aus = self.loaded_scaler.transform(features[0])
        predictions = self.loaded_model.predict(scaled_aus)
        predicted_emotions = self.loaded_label_encoder.inverse_transform(predictions)

        return predicted_emotions[0]