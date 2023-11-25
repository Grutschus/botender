import logging

from furhat_remote_api import FurhatRemoteApi  # type: ignore

from botender.perception.detectors.speech_detector import SpeechDetector
from botender.perception.perception_manager import PerceptionManager
from botender.webcam_processor import WebcamProcessor
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class InteractionGenerator(ABC):
    """Parent class for all interaction generators."""
    
    _furhat: FurhatRemoteApi
    _speech_detector: SpeechDetector
    _webcam_processor: WebcamProcessor
    _perception_manager: PerceptionManager

    def __init__(
        self,
        furhat: FurhatRemoteApi,
        speech_detector: SpeechDetector,
        webcam_processor: WebcamProcessor,
        perception_manager: PerceptionManager,
    ):
        self._furhat = furhat
        self._speech_detector = speech_detector
        self._webcam_processor = webcam_processor
        self._perception_manager = perception_manager

    @abstractmethod
    def generate_interaction(self):
        """Generates an interaction."""
        ...


class AttentionGenerator(InteractionGenerator):
    """Responsible for the regaining the attention of the user,
    after the user has walked away from the robot."""

    def generate_interaction(self):
        """Generates an interaction."""
        logger.info("Generating attention interaction...")


class DrinkRecommendationGenerator(InteractionGenerator):
    """Responsible for generating a drink recommendation and
    asking the user if they want to order it."""

    def generate_interaction(self):
        """Generates an interaction."""
        logger.info("Generating drink recommendation interaction...")


class GreetingGenerator(InteractionGenerator):
    """Responsible for generating a greeting."""

    def generate_interaction(self):
        """Generates an interaction."""
        logger.info("Generating greeting interaction...")


class IntroductionGenerator(InteractionGenerator):
    """Responsible for introducing the robot to the user and
    finding the name."""

    def generate_interaction(self):
        """Generates an interaction."""
        logger.info("Generating introduction interaction...")


class OpenDialogGenerator(InteractionGenerator):
    """Responsible for the open dialog at the end."""

    def generate_interaction(self):
        """Generates an interaction."""
        logger.info("Generating open dialog interaction...")
