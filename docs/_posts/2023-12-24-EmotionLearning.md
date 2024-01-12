---
layout: post
title: Expressing emotions
---
Our robotic bartender has now  mastered expressing emotions. Botender can convey feelings ranging from happiness to concern.


Botender selects a gesture based on the perceived emotion of the customer, using a randomization function to keep interactions unpredictable and varied. It can use the gestures in every other scenario of the interaction with the customer as well.


## Technical Background
Each gesture type, like 'happy', includes several JSON files, each representing a unique expression within that emotion. These files detail precise facial movements recorded through an iPhone.

The randomization function first retrieves a list of possible gestures for the specified type. If gestures are available, the function uses a random index within the range of the available gestures to select one. Its details are loaded from the corresponding JSON file. The gestures are used to:

- **Responding to emotional cues**: Botender utilizes the gesture system to respond to the perceived emotional state of customers. For instance, if the Perception Manager identifies a customer as happy, Botender may use a gesture from the 'happy' category.

- **Enhancing Conversational Context**:  Gestures are also used to complement Botender's verbal responses, adding context to conversations. For example, while listening to a customer, Botender might use a gesture from the 'listening' category to show attentiveness.

- **Dynamic Interaction Flow**: The gesture system is integrated into Botender's interaction flow, allowing it to seamlessly switch between different gestures based on the conversation's context and the customer's emotional state.

## Gesture Categories

We added gestures in the following categories:

- Concern
- Happy
- Idle
- Laugh
- Listening
- Thinking
- Misunderstanding

## Example: The Laugh Gesture

The following gif shows one of the laughing gestures:

![Laugh Gesture](../images/laugh_gif.gif "Laugh Gesture")