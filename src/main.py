from pyfeat_thread import PyfeatThread
from interaction_thread import InteractionThread
from webcam_thread import WebCamThread

# main function
if __name__ == "__main__":
    print("Main - Started.")
    webcam_thread = WebCamThread()
    pyfeat_thread = PyfeatThread(webcam_thread)
    interaction_thread = InteractionThread(pyfeat_thread, webcam_thread)
    webcam_thread.start()
    pyfeat_thread.start()
    interaction_thread.start()
    interaction_thread.join()
    pyfeat_thread.join()
    webcam_thread.join()
    print("Main - Program finished.")