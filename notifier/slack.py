import time
import os
from .notifier import Notifier
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from PIL import Image

class SlackNotifier(Notifier):

    def __init__(self, token, channel):
        self._slack_client = WebClient(token=token)
        self._channel = channel

    def notify(self, message, rgb_image_array):
        super().notify(message, rgb_image_array)

        # make a temporary image file as Slack can only work with files
        try:
            filename = f"/tmp/{int(time.time())}.png"
            Image.fromarray(rgb_image_array).save(filename) 
        except Exception as e:
            print(f"Error saving image {filename}:", e)
            return

        try:
            self._slack_client.chat_postMessage(
                channel=self._channel,
                text=message
            )

            self._slack_client.files_upload_v2(
                channel=self._channel,
                file=filename,
                title=message
            )

            print(f"Image sent successfully: {filename}")
            
        except SlackApiError as e:
            print("Error sending image to Slack:", e.response["error"])
        finally:
            # clean up the image
            os.remove(filename)
