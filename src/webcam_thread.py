from threading import Thread

# define the WebcamThread class
class WebCamThread(Thread):
    def __init__(self):
        super(WebCamThread, self).__init__()
        self.stopThreadFlag = False
        
    def showEmotion(self, emotion):
        print("WebcamThread - Current emotion: " + emotion)
    
    def showMessage(self, message):
        print("WebcamThread - Message: " + message)
    
    def stopThread(self):
        self.stopThreadFlag = True

    def run(self):
        print("WebcamThread - Started.")
        while not self.stopThreadFlag:
            pass
        print("WebcamThread - Finished.")