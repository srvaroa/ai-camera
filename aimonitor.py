import argparse
import signal
import sys
import os

from notifier.slack import SlackNotifier
from PIL import Image

def main():
    parser = argparse.ArgumentParser(description="Security Camera Application")
    parser.add_argument('--sensor', type=str, choices=['webcam', 'imx500'], required=True, help="Type of sensor to use: 'webcam' or 'imx500'")
    parser.add_argument('--channel', type=str, default=None, required=False, help="Id of the Slack channel to post notifications to")
    args = parser.parse_args()

    token = os.getenv("SLACK_TOKEN")
    if not token:
        raise ValueError("SLACK_TOKEN environment variable not set")

    notifier = SlackNotifier(token, args.channel)

    def on_event(metadata, frame):
        print("Event detected:", metadata)
        notifier.notify("Event detected", frame)

    if args.sensor == 'webcam':
        from sensor.webcam import WebcamSensor
        sensor = WebcamSensor(4, on_event)
    elif args.sensor == 'imx500':
        try:
            # avoid loading this unless we're explicitly using it
            # as we need picamera2, which may not be available on all platforms
            from sensor.imx500 import IMX500Sensor
        except ImportError:
            print("Error: picamera2 is not installed. Please install picamera2 to use the IMX500 sensor.")
            sys.exit(1)
        sensor = IMX500Sensor(onEvent=on_event, fps=4)

    def signal_handler(sig, frame):
        sensor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    sensor.start()

if __name__ == '__main__':
    main()
