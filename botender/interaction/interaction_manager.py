import logging
import time
from threading import Thread

import numpy as np
from furhat_remote_api import FurhatRemoteAPI  # type: ignore

from botender.interaction.gaze_coordinator import GazeClasses, GazeCoordinatorThread
from botender.interaction.gestures import get_random_gesture
from botender.interaction.interaction_coordinator import InteractionCoordinator
from botender.perception.perception_manager import PerceptionManager
from botender.webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)


# define the InteractionManagerThread class
class InteractionManagerThread(Thread):
    """The InteractionManagerThread is responsible for starting an interaction
    as soon as a face is detected.

    Currently, the interaction runs in the same thread, which means that the
    InteractionManager will start looking for new faces only after the
    interaction has finished.
    """

    _stopped: bool = False
    _perception_manager: PerceptionManager
    _webcam_processor: WebcamProcessor
    _gaze_coordinator: GazeCoordinatorThread
    _current_interaction: InteractionCoordinator | None = None
    _furhat: FurhatRemoteAPI
    _face_present_frame_counter: int = 0
    _run_loop_speed: float = 1.0  #  1.0 means 1 loop per second

    def __init__(
        self,
        perception_manager: PerceptionManager,
        webcam_processor: WebcamProcessor,
        furhat_remote_address: str,
        frame_width: int = 640,
        frame_height: int = 480,
        number_of_cells_per_side: int = 7,
    ):
        super(InteractionManagerThread, self).__init__(name="InteractionManagerThread")
        self._perception_manager = perception_manager
        self._webcam_processor = webcam_processor
        self._furhat = self._init_furhat(furhat_remote_address)
        self._gaze_coordinator = GazeCoordinatorThread(
            self._furhat,
            self._perception_manager,
            self._webcam_processor,
            frame_width,
            frame_height,
            number_of_cells_per_side,
        )

        logger.debug("Spawning GazeCoordinatorThread...")
        self._gaze_coordinator.start()

    def _init_furhat(self, furhat_remote_address: str) -> FurhatRemoteAPI:
        """Initializes the FurhatRemoteAPI object."""

        logger.debug("Initializing FurhatRemoteAPI...")
        furhat = FurhatRemoteAPI(furhat_remote_address)
        FACE = "Patricia"
        MASK = "Adult"
        VOICE = "BellaNeural"
        furhat.set_led(red=100, green=0, blue=0)
        furhat.set_face(character=FACE, mask=MASK)
        furhat.set_voice(VOICE)
        furhat.set_led(red=0, green=100, blue=0)
        logger.debug("FurhatRemoteAPI initialized.")
        return furhat

    def stopThread(self):
        """Stops the Gazecoordinator and the InteractionManagerThread. Sets furhat to
        idle state."""

        logger.debug("Received stop signal. Stopping InteractionManagerThread...")
        self._stopped = True
        logger.debug("Sending stop signal to GazeCoordinatorThread...")
        self._gaze_coordinator.stopThread()
        self._gaze_coordinator.join()
        logger.debug("GazeCoordinatorThread stopped.")
        # TODO: set furhat to idle state

    def _start_interaction(self):
        """Create a new InteractionCoordinator and launch the interaction."""

        logger.info("Starting interaction...")
        self._current_interaction = InteractionCoordinator(
            self._perception_manager,
            self._webcam_processor,
            self._gaze_coordinator,
            self._furhat,
        )

    def _should_start_interaction(self) -> bool:
        """Starts an interactino if a face is present for 150 consecutive frames."""

        return self._perception_manager.face_presence_counter > 150

    def run(self):
        """Starts the interaction as soon as a face is detected. Sets furhat to idle
        state when no face is detected."""

        logger.info("Started...")
        while not self._stopped:
            start_time = time.monotonic()

            if self._current_interaction is not None:
                self._current_interaction = self._current_interaction.interact()
            else:
                if self._should_start_interaction():
                    self._start_interaction()
                else:
                    self._gaze_coordinator.set_gaze_state(GazeClasses.IDLE)
                    # Trigger an idle gesture with a specific probability
                    # ~ 30 FPS -> 1 idle gesture every 5 seconds -> p = 1/150
                    if np.random.choice(690) <= 69:
                        gesture = get_random_gesture("idle")
                        self._furhat.gesture(body=gesture, blocking=False)

            end_time = time.monotonic()
            time.sleep(max(0, self._run_loop_speed - (end_time - start_time)))
            # else: randomly add whistles or other idle sounds and gestures
        logger.info("Received stop signal. Exiting...")
