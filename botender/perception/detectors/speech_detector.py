import logging

from furhat_remote_api import FurhatRemoteAPI  # type: ignore

logger = logging.getLogger(__name__)


class SpeechDetector:
    """The SpeechDetector is responsible for capturing speech from the user.
    It runs in the same thread as the InteractionManager."""

    _furhat: FurhatRemoteAPI

    def __init__(self, furhat: FurhatRemoteAPI):
        self._furhat = furhat

    def capture_speech(self) -> str:
        """Captures speech from the user and returns it as a string."""
        try:
            # Turn on LED to indicate listening
            self._furhat.set_led(red=200, green=50, blue=50)

            # Start listening for user speech
            speech_result = self._furhat.listen()

            # Turn off LED (reset to default or turn off completely)
            self._furhat.set_led(red=0, green=0, blue=0)

            # Check if the speech was successfully captured
            if speech_result.success:
                captured_speech = speech_result.message

                # Log the captured speech
                logger.info(f'Speech captured: "{captured_speech}"')

                return captured_speech
            else:
                # Handle the unsuccessful capture
                logger.error("Speech capture unsuccessful.")
                return ""

        except Exception as e:
            # Log the exception with stack trace
            logger.exception(f"Error in capture_speech: {e}")
            return ""
