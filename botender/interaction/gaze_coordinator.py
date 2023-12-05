import logging
import random
from enum import Enum
from threading import Thread

from furhat_remote_api import FurhatRemoteAPI  # type: ignore

from botender.perception.perception_manager import PerceptionManager
from botender.webcam_processor import Rectangle, WebcamProcessor

logger = logging.getLogger(__name__)

GAZE_SCALE_COEFFICIENT = 0.2
GAZE_HEIGHT_COEFFICIENT = 0.05

# The gaze z value is calculated as follows:
# gaze_z = GAZE_Z_MAX - (GAZE_Z_DECREASE * (face_width / frame_width))
GAZE_Z_MAX = 4
GAZE_Z_DECREASE = 12.63


class GazeClasses(Enum):
    """The GazeClasses enum represents the different gaze classes that can be used
    to coordinate the gaze of the robot.
    """

    NONE = 0
    """The robot should look down."""

    FACE = 1
    """The robot should look at the face of the user."""

    IDLE = 2
    """The robot should look around."""


class GazeCoordinatorThread(Thread):
    """The GazeCoordinatorThread is responsible for coordinating the gaze of the robot.
    It is linked to an InteractionCoordinator and receives the gaze commands from it.
    """

    _furhat: FurhatRemoteAPI
    _perception_manager: PerceptionManager
    _webcam_processor: WebcamProcessor
    _stopped: bool = False
    _state: GazeClasses = GazeClasses.NONE

    # Number of cells per row and column in the grid. It has to be an odd number.
    _number_of_cells_per_side: int
    _frame_width: int = 640
    _frame_height: int = 480

    _grid: list[Rectangle] = []
    _last_face_cell: int = -1
    _last_idle_location: str = "0,0,0"

    def __init__(
        self,
        furhat: FurhatRemoteAPI,
        perception_manager: PerceptionManager,
        webcam_processor: WebcamProcessor,
        frame_width: int = 640,
        frame_height: int = 480,
        number_of_cells_per_side: int = 7,
    ):
        super(GazeCoordinatorThread, self).__init__()
        self._furhat = furhat
        self._perception_manager = perception_manager
        self._webcam_processor = webcam_processor
        self._frame_width = frame_width
        self._frame_height = frame_height
        self._number_of_cells_per_side = number_of_cells_per_side
        self._init_grid()

    def stopThread(self):
        """Stops the GazeCoordinatorThread."""

        logger.debug("Received stop signal. Stopping GazeCoordinatorThread...")
        self._stopped = True

    def run(self):
        """Runs the GazeCoordinatorThread. Renders the gaze state to the screen
        such that Furhat follows his interaction partner."""

        while not self._stopped:
            # Render the gaze state to the screen
            if self._state == GazeClasses.NONE:
                self._handle_none()
            elif self._state == GazeClasses.IDLE:
                self._handle_idle()
            elif self._state == GazeClasses.FACE:
                self._handle_attend_face()

    def _init_grid(self):
        """Initializes the grid and adds it to the gui."""

        # Calculate the size of a cell
        cell_width = self._frame_width / self._number_of_cells_per_side
        cell_height = self._frame_height / self._number_of_cells_per_side

        # Initialize the grid
        self._grid = []
        for i in range(self._number_of_cells_per_side):
            for j in range(self._number_of_cells_per_side):
                self._grid.append(
                    (
                        (i * cell_width, j * cell_height),
                        ((i + 1) * cell_width, (j + 1) * cell_height),
                    )
                )

        self._webcam_processor.add_rectangles_to_current_frame(
            self._grid, color=(0, 0, 255), modifier_key="grid"
        )

    def _handle_none(self):
        """Handles the none gaze command."""

        # Look down
        location = "0,-1.0,1.0"

        # Call the attend function of the furhat remote api
        self._furhat.attend(location=location)

    def _handle_idle(self):
        """Handles the idle gaze command."""

        # Get the values of the last idle location
        x, y, z = self._last_idle_location.split(",")

        # Add random noise to the location
        x = float(x) + random.uniform(-0.01, 0.01)
        y = float(y) + random.uniform(-0.01, 0.01)
        z = 0.5

        location = f"{x},{y},{z}"

        # Call the attend function of the furhat remote api
        self._furhat.attend(location=location)

    def _handle_attend_face(self):
        """Handles the attend_face gaze command."""

        try:
            # Get the current face from the perception manager. Select the first face if more than one is present.
            face = self._perception_manager.current_result.faces[0]
        except IndexError:
            return

        # Log width and height of face
        self._webcam_processor.update_debug_info("face width", f"{face[1][0] - face[0][0]}")

        # Get the cell of the face
        cell = self._get_cell_of_face(face)

        # Calculate the center of the cell
        cell_center = (
            (self._grid[cell][0][0] + self._grid[cell][1][0]) / 2,
            (self._grid[cell][0][1] + self._grid[cell][1][1]) / 2,
        )

        # Calculates the location that furhat should look at
        frame_center = (self._frame_width / 2, self._frame_height / 2)
        x = (
            (frame_center[0] - cell_center[0])
            / (self._frame_width / 2)
            * GAZE_SCALE_COEFFICIENT
        )
        y = (
            ((frame_center[1] - cell_center[1])
            / (self._frame_height / 2) + GAZE_HEIGHT_COEFFICIENT)
            * GAZE_SCALE_COEFFICIENT
        )
        z = GAZE_Z_MAX - (GAZE_Z_DECREASE * ((face[1][0] - face[0][0]) / self._frame_width))
        location = f"{x},{y},{z}"
        self._webcam_processor.update_debug_info("Gaze Location", location)

        # Call the attend function of the furhat remote api if the face is in a different cell than the last face
        if cell != self._last_face_cell:
            self._furhat.attend(location=location)
            self._last_face_cell = cell

    def _get_cell_of_face(self, face: Rectangle) -> int:
        """Returns the cell index of the given face.
        If the face is not in the grid, -1 is returned."""

        # Calculate the center of the face
        face_center = (
            (face[0][0] + face[1][0]) / 2,
            (face[0][1] + face[1][1]) / 2,
        )

        # Find the cell that contains the face
        for i in range(len(self._grid)):
            if (
                self._grid[i][0][0] <= face_center[0] <= self._grid[i][1][0]
                and self._grid[i][0][1] <= face_center[1] <= self._grid[i][1][1]
            ):
                return i

        return -1

    def set_gaze_state(self, state: GazeClasses):
        """Sets the gaze state of the robot."""

        if self._state != state:
            self._state = state
            logger.info(f"Setting gaze state to {state}")
            #self._webcam_processor.update_debug_info("Gaze State", self._state)
