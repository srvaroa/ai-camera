import argparse
import signal
import sys
import os

from PIL import Image

def main():
    parser = argparse.ArgumentParser(description="Security Camera Application")
    parser.add_argument('--sensor', type=str, choices=['webcam', 'imx500'], required=True, help="Type of sensor to use: 'webcam' or 'imx500'")
    parser.add_argument('--slack', type=str, default=None, required=False, help="POst notifications to the given slack channel, using the given slack token in SLACK_TOKEN")
    parser.add_argument('--console', action='store_true', help="Print notifications to console")
    args = parser.parse_args()

    if args.slack:
        token = os.getenv("SLACK_TOKEN")
        if not token:
            raise ValueError("SLACK_TOKEN environment variable not set")
        from notifier.slack import SlackNotifier
        notifier = SlackNotifier(token, args.channel)
    elif args.console:
        from notifier.console import ConsoleNotifier
        notifier = ConsoleNotifier()

    def on_event(metadata, frame):
        notifier.notify(metadata, frame)

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
