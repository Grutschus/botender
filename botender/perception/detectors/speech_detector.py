import logging
from furhat_remote_api import FurhatRemoteApi  # type: ignore

logger = logging.getLogger(__name__)


class SpeechDetector:
    """The SpeechDetector is responsible for capturing speech from the user.
    It runs in the same thread as the InteractionManager."""

    _furhat: FurhatRemoteApi

    def __init__(self, furhat: FurhatRemoteApi):
        self._furhat = furhat

    def capture_speech(self):
        """Captures speech from the user and returns it as an array of strings."""

        raise NotImplementedError
