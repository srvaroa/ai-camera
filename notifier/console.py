import time
import os
from .notifier import Notifier

class ConsoleNotifier(Notifier):

    def __init__(self):
        pass

    def notify(self, message, rgb_image_array):
        super().notify(message, rgb_image_array)
        print(message)
