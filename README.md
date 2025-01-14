# People detection and notifications based on the Raspberry Pi + AI Camera (Sony IMX500)

This project is a **proof of concept** based on the [Raspberry Pi AI
camera](https://www.raspberrypi.com/documentation/accessories/ai-camera.html),
equipped with the Sony IMX500 imaging sensor, which allows running
vision AI models even with very limited hardware (e.g. the project has
been tested on a Raspberry Pi 3 model B).

For testing purposes, the application can also run in a Linux laptop
with a standard webcam. In this configuration, it uses a light-weight,
pre-trained SSD MobileNetV2 model on CPU.

## Disclaimer

This is an experiment, for fun. Expect rough edges and opinionated
choices. For example, the only notification target supported in this
version is Slack just because it suited my needs. In any case, it's
trivial to add support for other sensors, other notification targets
(e.g. s3 bucket, email, etc.)

## Requirements

- **Python 3.10 or higher**
- **Raspberry Pi hardware**:
  - Raspberry Pi (ideally 4 or 5, I've tested successfully with 3B)
  - IMX500 AI camera

## Setup

### 1. Hardware

To set up the Raspberry Pi AI camera, refer to the [official documentation](https://www.raspberrypi.com/documentation/accessories/ai-camera.html#getting-started).

For testing, any Linux system with a webcam should do it (including a Raspberry
Pi, although expect it to be slow if the model runs on the CPU)

### 2. Prepare the environment

    pip install -r requirements.txt

### 3. Run the application

    python3 aimonitor.py --sensor=[webcam|imx500] --channel=<SLACK_CHANNEL_ID>

Use `imx500` when using the RPi AI Camera, or`webcam` if testing with a webcam.

To use the Slack notifier you need to provide a [bot
token](https://api.slack.com/tutorials/tracks/getting-a-token) in a
`SLACK_TOKEN` environment variable.
