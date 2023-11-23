from pyfeat_thread import PyfeatThread
from interaction_thread import InteractionThread
from webcam_thread import WebCamThread

# main function
if __name__ == "__main__":
    print("Main - Started.")
    webCamThread = WebCamThread()
    pyFeatThread = PyfeatThread(webCamThread)
    interactionThread = InteractionThread(pyFeatThread, webCamThread)
    webCamThread.start()
    pyFeatThread.start()
    interactionThread.start()
    interactionThread.join()
    pyFeatThread.join()
    webCamThread.join()
    print("Main - Program finished.")