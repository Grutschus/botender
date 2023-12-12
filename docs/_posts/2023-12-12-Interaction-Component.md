---
layout: post
title: Interaction Component
---
Botender's behavior  is adapted in real-time to respond appropriately to the user's emotions and the context of the interaction. The Interaction Component integrates perception data with a state machine approach. 

## Components and their functionality

- The **InteractionManager** Thread starts and manages the interactions. It waits for a face to be detected by the *Perception Manager* and initiates an interaction sequence. It also manages the current interaction state and delegates tasks to the *Interaction Coordinator*.

- The **GazeCoordinator** Thread manages Botender's gaze, ensuring it follows the user or adopts an idle state when no interaction is taking place. By utilizing frame dimensions and perception data, it calculates where Botender should look. That is how a more engaging interaction is created.

- The **InteractionCoordinator** follows the state design pattern. It manages different states. Each state encapsulates specific behaviors and responses. The transitions between states are based on user input, perceived emotions, and interaction progress.

## State Machine Dynamics
The *Interaction Manager* utilizes a FSM to manage the flow of interaction between Botender and the customer. It monitors whether the user is present in the frame. If the user leaves the frame, it is detected as an event, triggering the FSM to reset to its initial state: the `Greeting state`.Thus, a consistens experience is provided since the interaction starts from the beginning.

The use of a FSM allows for a rule-based conversation flow with Botender. Hence, the FSM provides a predictable flow of interaction, where each state can be developed and tested independently. This enhances maintainability.

The states in Botender's Interaction Manager are listed below:
- The `Greeting State`: It initiates the interaction with a welcoming message. Botender greets the user using pre-defined phrases and gestures. After the greeting is completed, the FSM transitions to the Introduction State. 
- The `Introduction State`: This state involves listening to the user's response and extracting the user's name using natural language processing techniques. It handles the introduction of the user to the robot. 
- The `Acknowledge Emotion State`: This state acknowledges the user's current emotional state as determined by the User Perception subsystem. It responds with appropriate gestures and comments based on the perceived emotion. To conclude the interaction, it leads to the Farewell State.
- The `Farewell State`: The final state which concludes the interaction. Botender bids farewell to the user with a friendly and positive gesture.
- The `Search State`: 

At any state, the system may return to the Greeting State, if the user disappears.
