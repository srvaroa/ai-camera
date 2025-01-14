
class Sensor():

    def __init__(self, fps=1.0, onEvent=None):
        self._onEvent = onEvent
        self._fps = fps

    def start(self):
        pass

    def stop(self):
        pass