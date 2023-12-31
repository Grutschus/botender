from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Literal

import numpy as np
from furhat_remote_api import FurhatRemoteAPI  # type: ignore
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pkg_resources import resource_filename

from botender.interaction import gestures
from botender.interaction.drink_recommendation import DrinkRecommender
from botender.interaction.gaze_coordinator import GazeClasses, GazeCoordinatorThread
from botender.perception.detectors.speech_detector import SpeechDetector
from botender.perception.perception_manager import PerceptionManager
from botender.webcam_processor import WebcamProcessor

logger = logging.getLogger(__name__)

DRINKS_DATA_PATH = resource_filename(
    __name__, "drinks/drinks_with_categories_and_ranks.csv"
)


def get_openai_response(messages: list[ChatCompletionMessageParam]) -> str:
    """Returns the response from OpenAI API"""
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    if (answer := response.choices[0].message.content) is None:
        raise ValueError("OpenAI API returned None")
    return answer


def get_valence_from_message(message: str) -> Literal["Positive"] | Literal["Negative"]:
    """Returns the valence from the message"""

    if os.getenv("ENABLE_OPENAI_API") != "True":
        return "Positive"

    chat_messages = [
        {
            "role": "system",
            "content": 'You are an endpoint.\nYou will receive a text that a user said upon asking a question.\n\nLook for the valence of the user in the text.\nIf you are certain about the valence return it.\nIf you are uncertain, only return "Error".\n\nThe response should have the following structure:\n\n[VALENCE OR ERROR]\n\nExamples:\nInput: "Ah yeah this drink sounds tasty!"\n\nYour response:\nPositive\n\nInput: "That doesn\'t sound very convincing."\n\nYour response:\nNegative',
        },
        {
            "role": "user",
            "content": message,
        },
    ]
    try:
        valence = get_openai_response(chat_messages)  # type: ignore[arg-type]
        if valence == "Error":
            raise ValueError("OpenAI API returned Error")
        if valence not in ["Positive", "Negative"]:
            raise ValueError("OpenAI API returned invalid valence")
    except ValueError as e:
        raise ValueError from e

    return valence  # type: ignore[return-value]


class InteractionCoordinator:
    """The InteractionCoordinator is responsible for coordinating the interaction and starting
    gaze coordination thread.

    It follows the `state` design pattern. The `InteractionCoordinator` is the context.
    More info here: https://refactoring.guru/design-patterns/state"""

    _perception_manager: PerceptionManager
    _webcam_processor: WebcamProcessor
    _speech_detector: SpeechDetector
    _gaze_coordinator: GazeCoordinatorThread
    _furhat: FurhatRemoteAPI
    _recommender: DrinkRecommender
    _state: InteractionState
    _previous_state: InteractionState | None
    user_info: dict[str, str]

    def __init__(
        self,
        perception_manager: PerceptionManager,
        webcam_processor: WebcamProcessor,
        gaze_coordinator: GazeCoordinatorThread,
        furhat: FurhatRemoteAPI,
    ):
        self._perception_manager = (
            perception_manager  # Used to get results from perception subsystem
        )
        self._webcam_processor = webcam_processor  # Used to interact with GUI
        self._furhat = furhat  # Used to interact with Furhat
        self._gaze_coordinator = gaze_coordinator
        self._recommender = DrinkRecommender(DRINKS_DATA_PATH)
        self._speech_detector = SpeechDetector(self._furhat)
        self._state = None  # type: ignore[assignment]
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
        self._furhat.gesture(
            body=gestures.get_random_gesture("listening"), blocking=False
        )
        return self._speech_detector.capture_speech()

    def get_emotion(self) -> str:
        """Returns the emotion of the user."""
        while self._perception_manager.detects_emotion():
            time.sleep(1)
        if self._perception_manager.current_result is None:
            return "neutral"
        return self._perception_manager.current_result.emotion

    def set_gaze(self, gaze_class: GazeClasses) -> None:
        """Sets the gaze to follow the user."""
        self._gaze_coordinator.set_gaze_state(gaze_class)

    def interact(self) -> InteractionCoordinator | None:
        """Runs one interaction cycle and returns the updated InteractionCoordinator or
        None if the interaction is finished."""

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
                    break

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

        # Set the gaze to follow the user
        self.context.set_gaze(GazeClasses.FACE)

        # Greet the user
        furhat.gesture(name="Smile", blocking=False)
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

    @staticmethod
    def get_name_from_message(message: str) -> str:
        """Returns the name from the message"""

        if os.getenv("ENABLE_OPENAI_API") != "True":
            return "Paul"

        chat_messages = [
            {
                "role": "system",
                "content": 'You are an endpoint.\nYou will receive a text that a user said upon asking for his/her name.\n\nLook for the name of the user in the text.\nIf you are certain about the name return it.\nIf you are uncertain, only return "Error".\n\nThe response should have the following structure:\n\n[NAME OR ERROR]\n\nExamples:\nInput: "Ah yeah so good to meet you how exciting I\'m John by the way"\n\nYour response:\nJohn\n\nInput: "I have never seen anything like you Botender."\n\nYour response:\nError',
            },
            {
                "role": "user",
                "content": message,
            },
        ]
        try:
            name = get_openai_response(chat_messages)  # type: ignore[arg-type]
            if name == "Error":
                raise ValueError("OpenAI API returned Error")
        except ValueError as e:
            raise ValueError from e

        return name

    def handle(self):
        furhat = self.context._furhat
        introduction_question = self.INTRODUCTION_QUESTIONS[
            np.random.randint(0, len(self.INTRODUCTION_QUESTIONS))
        ]
        # TODO Add gestures
        furhat.say(text=introduction_question, blocking=True)

        self._context._perception_manager.detect_emotion()
        user_response = self.context.listen()

        try:
            name = self.get_name_from_message(user_response)
        except ValueError:
            furhat.gesture(
                body=gestures.get_random_gesture("understand_issue"),
                blocking=False,
            )
            furhat.say(text="I'm sorry, I didn't quite get that.", blocking=True)
            return

        self.context.user_info["name"] = name

        furhat.gesture(name="Smile", blocking=False)
        furhat.say(
            text=f"Nice to meet you {self.context.user_info['name']}.", blocking=True
        )
        self.context.transition_to(AcknowledgeEmotionState())


class AcknowledgeEmotionState(InteractionState):
    """State to handle aknowledging the user's emotion"""

    def handle(self):
        furhat = self.context._furhat

        emotion = self.context.get_emotion()
        if emotion == "happy" or emotion == "neutral":
            furhat.gesture(body=gestures.get_random_gesture("happy"), blocking=False)
        elif emotion == "sad" or emotion == "angry":
            furhat.gesture(body=gestures.get_random_gesture("concern"), blocking=False)

        furhat.say(text=f"You seem a bit {emotion}.", blocking=True)
        self.context.transition_to(AskDrinkState())


class AskDrinkState(InteractionState):
    """State to start the drink recommendation flow"""

    DRINK_QUESTIONS = [
        "Can I interest you in a drink?",
        "Would you like a drink?",
        "How about a drink?",
        "Are you in the mood for a drink?",
    ]

    def handle(self):
        furhat = self.context._furhat
        drink_question = self.DRINK_QUESTIONS[
            np.random.randint(0, len(self.DRINK_QUESTIONS))
        ]
        furhat.say(text=drink_question, blocking=True)

        user_response = self.context.listen()

        try:
            valence = get_valence_from_message(user_response)
        except ValueError:
            furhat.gesture(
                body=gestures.get_random_gesture("understand_issue"),
                blocking=False,
            )
            furhat.say(text="I'm sorry, I didn't quite get that.", blocking=True)
            return

        if valence == "Positive":
            furhat.gesture(body=gestures.get_random_gesture("happy"), blocking=False)
            furhat.say(text="That's great!", blocking=True)
            self.context.transition_to(AskTastePreference())
        elif valence == "Negative":
            furhat.gesture(body=gestures.get_random_gesture("concern"), blocking=False)
            furhat.say(
                text="Alright, just let me know if you change your mind", blocking=True
            )
            self.context.transition_to(FarewellState())


class AskTastePreference(InteractionState):
    TASTE_PREFERENCE_QUESTIONS = [
        "What kind of cocktail do you like? I have sweet, milk-based, sour, and strong cocktails.",
        "My cocktails are sour, sweet, milk-based, or strong. What do you prefer?",
    ]

    TASTE = Literal["Sour", "Sweet", "Milk-based", "Strong"]

    def get_taste_preference_from_message(self, message: str) -> TASTE:
        """Returns the taste preference from the message"""

        if os.getenv("ENABLE_OPENAI_API") != "True":
            return "Sour"

        chat_messages = [
            {
                "role": "system",
                "content": 'You are an endpoint.\nYou will receive a text that a user said upon asking for his/her taste preference. Available tastes are Sweet, Sour, Milk-based, and Strong.\n\nLook for the taste preference of the user in the text.\nIf you are certain about the taste preference return it.\nIf you are uncertain, only return "Error".\n\nThe response should have the following structure:\n\n[TASTE PREFERENCE OR ERROR]\n\nExamples:\nInput: "I like sweet cocktails."\n\nYour response:\nSweet\n\nInput: "I want something heavy with a lot of alcohol."\n\nYour response:\nStrong',
            },
            {
                "role": "user",
                "content": message,
            },
        ]
        try:
            taste_preference = get_openai_response(chat_messages)  # type: ignore[arg-type]
            if taste_preference == "Error":
                raise ValueError("OpenAI API returned Error")
            if taste_preference not in ["Sour", "Sweet", "Milk-based", "Strong"]:
                raise ValueError("OpenAI API returned invalid taste preference")
        except ValueError as e:
            raise ValueError from e

        return taste_preference  # type: ignore[return-value]

    def handle(self):
        furhat = self.context._furhat

        taste_preference_question = self.TASTE_PREFERENCE_QUESTIONS[
            np.random.randint(0, len(self.TASTE_PREFERENCE_QUESTIONS))
        ]
        furhat.say(text=taste_preference_question, blocking=True)

        user_response = self.context.listen()

        try:
            taste_preference = self.get_taste_preference_from_message(user_response)
        except ValueError:
            furhat.gesture(
                body=gestures.get_random_gesture("understand_issue"),
                blocking=False,
            )
            furhat.say(text="I'm sorry, I didn't quite get that.", blocking=True)
            return

        self.context.user_info["taste_preference"] = taste_preference

        self.context.transition_to(RecommendDrinksState())


class RecommendDrinksState(InteractionState):
    """State to start the drink recommendation flow"""

    def generate_cocktail_description(self, message: str):
        """Returns a cocktail description based on the ingredients"""

        if os.getenv("ENABLE_OPENAI_API") != "True":
            return "This cocktail has a great balance between sour and sweet."

        chat_messages = [
            {
                "role": "system",
                "content": 'You are an endpoint. You will receive a cocktail name along with its ingredients. Your task is to generate an enticing but short description of the cocktail in the following format: I can recommend you a "cocktailname". It is _ Examples: Input:  KING OF KINGSTON,"1 ounce gin, 1 teaspoon grapefruit, Â½ ounce crÃ¨me de, 1 teaspoon grenadine, 1 ounce pineapple juice1 ounce heavy cream, 1 ounce dark rum, 1 ounce light rum, Â½ ounce cherry brandy 1 pineapple slice, 4 ounces pineapple juiceYour response: I can recommend you a King of Kingston. It is a delightful mix with a high sweetness score, combining the unique flavors of grapefruit and pineapple with a touch of creamy crème de cacao.'
            },
            {
                "role": "user",
                "content": message,
            },
        ]
        try:
            cocktail_description = get_openai_response(chat_messages)  # type: ignore[arg-type]
            if cocktail_description == "Error":
                raise ValueError("OpenAI API returned Error")
        except ValueError as e:
            raise ValueError from e

        return cocktail_description  # type: ignore[return-value]

    def handle(self):
        recommender = self.context._recommender
        furhat = self.context._furhat
        emotion = self.context.get_emotion()

        taste_preference = "Sour"

        # Call the recommend_drink method to get a recommendation
        random_recommendation = recommender.recommend_drink(emotion, taste_preference)

        # Since the recommendation is a DataFrame, extract the first row
        # and access the 'Cocktail' and 'Ingredients' columns
        if not random_recommendation.empty:
            cocktail_name = random_recommendation["Cocktail"].iloc[0]
            ingredients = random_recommendation["Ingredients"].iloc[0]
            cocktail_info = f'name: "{cocktail_name}" , ingredients: {ingredients}'


            try:
                cocktail_description = self.generate_cocktail_description(cocktail_info)    
                furhat.say(text=cocktail_description, blocking=True)            

            except ValueError:
                furhat.gesture(
                    body=gestures.get_random_gesture("understand_issue"),
                    blocking=False,
                )
                furhat.say(text="I'm sorry, I am having an error, please wait.", blocking=True)
                return

        else:
            answer = "No recommendation available for the given criteria."

        furhat.say(
            text="If that sounds good to you, I will get started right away.",
            blocking=True,
        )

        user_response = self.context.listen()

        try:
            valence = get_valence_from_message(user_response)
        except ValueError:
            furhat.gesture(
                body=gestures.get_random_gesture("understand_issue"),
                blocking=False,
            )
            furhat.say(text="I'm sorry, I didn't quite get that.", blocking=True)
            return

        if valence == "Positive":
            furhat.gesture(body=gestures.get_random_gesture("happy"), blocking=False)
            furhat.say(text="That's great!", blocking=True)
            furhat.say(text=f"Here is your {cocktail_name}", blocking=True)
            self.context.transition_to(FarewellState())
        elif valence == "Negative":
            furhat.gesture(body=gestures.get_random_gesture("concern"), blocking=False)
            furhat.say(
                text="Alright, I will look up another cocktail", blocking=True
            )
        


class FarewellState(InteractionState):
    """State to handle saying goodbye to the user"""

    def handle(self):
        furhat = self.context._furhat
        furhat.gesture(name="BigSmile", blocking=False)
        furhat.say(text="Goodbye!", blocking=True)

        time.sleep(10)


class SearchState(InteractionState):
    """State to handle looking for the user"""

    def handle(self):
        furhat = self.context._furhat

        furhat.gesture(
            body=gestures.get_random_gesture("understand_issue"), blocking=False
        )
        furhat.say(text="Where did you go?", blocking=True)

        self.context.transition_to(FarewellState())
