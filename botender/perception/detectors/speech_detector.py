import logging
from furhat_remote_api import FurhatRemoteApi  # type: ignore

logger = logging.getLogger(__name__)


class SpeechDetector:
    _furhat: FurhatRemoteApi

    def __init__(self, furhat: FurhatRemoteApi):
        self._furhat = furhat

    def capture_speech(self):
        raise NotImplementedError
