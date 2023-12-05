from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod

import numpy as np
from furhat_remote_api import FurhatRemoteAPI  # type: ignore
from openai import OpenAI

from botender.perception.detectors.speech_detector import SpeechDetector
from botender.perception.perception_manager import PerceptionManager
from botender.webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)


class InteractionCoordinator:
    """The InteractionCoordinator is responsible for coordinating the interaction and starting
    gaze coordination thread.

    It follows the `state` design pattern. The `InteractionCoordinator` is the context.
    More info here: https://refactoring.guru/design-patterns/state"""

    _perception_manager: PerceptionManager
    _webcam_processor: WebcamProcessor
    _speech_detector: SpeechDetector
    _furhat: FurhatRemoteAPI
    _state: InteractionState
    _previous_state: InteractionState | None
    user_info: dict[str, str]

    def __init__(
        self,
        perception_manager: PerceptionManager,
        webcam_processor: WebcamProcessor,
        furhat: FurhatRemoteAPI,
    ):
        self._perception_manager = (
            perception_manager  # Used to get results from perception subsystem
        )
        self._webcam_processor = webcam_processor  # Used to interact with GUI
        self._furhat = furhat  # Used to interact with Furhat
        self._speech_detector = SpeechDetector(self._furhat)
        self._state = None
        self.transition_to(GreetingState())  # Initial state
        self.user_info = {}

    def transition_to(self, state: InteractionState):
        """The Context allows changing the State object at runtime."""
        logger.info(f"Interaction state transitioned to {type(state).__name__}")
        self._previous_state = self._state
        self._state = state
        self._state.context = self

    def handle(self):
        """The Context delegates part of its behavior to the current State object."""
        self._state.handle()

    def listen(self) -> str:
        """Listens to the user and returns the text."""
        # TODO Remove try catch
        try:
            return self._speech_detector.capture_speech()
        except NotImplementedError:
            return self._furhat.listen().message

    def interact(self) -> InteractionCoordinator:
        """Runs one interaction cycle and returns the updated InteractionCoordinator."""

        self.handle()

        if isinstance(self._state, FarewellState):
            self.handle()  # One more time to say goodbye
            logger.info("Interaction finished.")
            return None

        # If no face is present, transition to search state
        if not self._perception_manager.face_present and not isinstance(
            self._state, SearchState
        ):
            timeout = 0.0
            while not self._perception_manager.face_present:
                logger.info("No face present.")
                time.sleep(0.5)
                timeout += 0.5
                if timeout > 3:
                    logger.info("Timeout reached.")
                    self.transition_to(SearchState())

        return self


class InteractionState(ABC):
    """Abstract class for all interaction states."""

    @property
    def context(self) -> InteractionCoordinator:
        return self._context

    @context.setter
    def context(self, context: InteractionCoordinator):
        self._context = context

    @abstractmethod
    def handle(self):
        """Handles the interaction."""
        ...


class GreetingState(InteractionState):
    """State to handle greeting the user"""

    GREETINGS: list[str] = [
        "Hello there! I am Botender, your friendly neighborhood robotic bartender.",
        "Hey hey, I am Botender, the robotic bartender.",
        "Greetings, soo good to see you! My name is Botender.",
        "Hello, I am Botender, your friendly robotic bartender.",
    ]

    def handle(self):
        furhat = self.context._furhat

        # Greet the user
        greeting = self.GREETINGS[np.random.randint(0, len(self.GREETINGS))]

        # TODO Add gestures
        furhat.say(text=greeting, blocking=True)

        # Transition to introduction state
        self.context.transition_to(IntroductionState())


class IntroductionState(InteractionState):
    """State to handle introducing the user to the robot"""

    INTRODUCTION_QUESTIONS: list[str] = [
        "What is your name?",
        "And who might you be?",
        "What is your name, if I may ask?",
        "It's a pleasure to meet you! What is your name?",
    ]

    def handle(self):
        furhat = self.context._furhat
        introduction_question = self.INTRODUCTION_QUESTIONS[
            np.random.randint(0, len(self.INTRODUCTION_QUESTIONS))
        ]
        # TODO Add gestures
        furhat.say(text=introduction_question, blocking=True)

        user_response = self.context.listen()

        if os.getenv("ENABLE_OPENAI_API") != "True":
            self.context.user_info["name"] = "Paul"
        else:
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": 'You are an endpoint.\nYou will receive a text that a user said upon asking for his/her name.\n\nLook for the name of the user in the text.\nIf you are certain about the name return it.\nIf you are uncertain, only return "Error".\n\nThe response should have the following structure:\n\n[NAME OR ERROR]\n\nExamples:\nInput: "Ah yeah so good to meet you how exciting I\'m John by the way"\n\nYour response:\nJohn\n\nInput: "I have never seen anything like you Botender."\n\nYour response:\nError',
                    },
                    {
                        "role": "user",
                        "content": user_response,
                    },
                ],
                temperature=1,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

            name = response.choices[0].message.content
            if name == "Error":
                furhat.say(text="I'm sorry, I didn't quite get that.", blocking=True)
                return
            self.context.user_info["name"] = name

        furhat.say(
            text=f"Nice to meet you {self.context.user_info['name']}.", blocking=True
        )
        self.context.transition_to(AcknowledgeEmotionState())


class AcknowledgeEmotionState(InteractionState):
    """State to handle aknowledging the user's emotion"""

    def handle(self):
        self.context.transition_to(FarewellState())


class FarewellState(InteractionState):
    """State to handle saying goodbye to the user"""

    def handle(self):
        furhat = self.context._furhat
        furhat.say(text="Goodbye!", blocking=True)


class SearchState(InteractionState):
    """State to handle looking for the user"""

    def handle(self):
        pass
