---
layout: post
title: User Perception Framework
---
  
After laying the foundational architecture of the Botender framework, our next step is to implement the User Perception Framework. 
### Framework Components and Their Roles
- The **EmotionDetector** predicts the customer's emotional state by utilizing a Support Vector Machine (SVC) model. The model is trained based on the dataset DiffusionFER provided on Studium. It is loaded from a pre-trained file. 

- The **FacialExpressionDetector** detects faces in a frame and returns their coordinates as rectangles. It also extracts facial features, landmarks and action units, from the detected faces and returns them. Thus, the detector provides the raw data for the **Emotion detector**.

- The **SpeechDetector** captures and processes spoken language from customers. The `furhat_remote_api` is used for capturing speech. To indicate active listening the Furhat's LED is turned on. 

- The **DetectionWorker** runs as a separate process and ensures that Botender is responsive, even under the load of real-time video processing. It handles the face and emotion detection. This class provides the following features:
    - Utilizes **FacialExpressionDetector** and **EmotionDetector** for processing frames. 
    - Manages a shared array for frame data and uses events for process synchronization.
    - Implements a method to detect emotion periodically based on frame counts and skips.

- The **PerceptionManager** manages, and initializes the **DetectionWorker** process, as well as the overall perception workflow. 
It uses multiprocessing primitives for inter-process communications: 
    - a  `mp.Queue` for task management 
    - a `mp.Pipe` for result transmission
    - shared memory `mp.Array`
    - synchronization between main process (**PerceptionManager**) and child process (**DetectionWorker**) through initializing `mp.Event` objects      

    Furthermore, the class contains methods to trigger emotion detection and render results (faces and emotions) onto the current frame.
