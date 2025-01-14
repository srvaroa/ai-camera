import cv2
import time
import torch
from torchvision import models, transforms
from torchvision.models.detection import ssdlite320_mobilenet_v3_large
from .sensor import Sensor

# Emulates a sensor based on the webcam feed, and detects people using a pre-trained SSD MobileNetV2 model
class WebcamSensor(Sensor):

    # fps: Frames per second
    # onEvent: Callback function to be called when an event is detected
    # preview: Whether to display the webcam feed in a window
    def __init__(self, fps, onEvent, preview=False):
        super().__init__(fps, onEvent)
        self._preview = preview
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            self.cap = None
        else:
            self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)               
        self.model = ssdlite320_mobilenet_v3_large(pretrained=True)
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.ToTensor()
        ])
        self.__running = False

    def capture_and_process(self):
        while self.__running:

            # drain buffer, relevant specially with low fps
            for _ in range(10):
                self.cap.read()

            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break

            # Convert the frame to a tensor and run it through the model
            input_tensor = self.transform(frame)
            start_time = time.time()
            with torch.no_grad():
                predictions = self.model([input_tensor])
            end_time = time.time()
            inference_time = end_time - start_time

            # Check if any person is detected and draw bounding boxes
            for prediction in predictions:
                for box, label, score in zip(prediction['boxes'], prediction['labels'], prediction['scores']):
                    if label == 1 and score > 0.5:  # Label 1 is for 'person' in COCO dataset
                        x1, y1, x2, y2 = box.int().tolist()  # Convert to integers
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        print(f"Detected in {inference_time:.4f}s")
                        self._onEvent(f"person", frame[:, :, ::-1]) # Convert BGR to RGB
                        break

            # Display the frame
            if self.__running and self._preview:
                cv2.imshow('Webcam', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop()
                    break
            
            time.sleep(1 / self._fps)

    def start(self):
        self.__running = True
        self.capture_and_process()

    def stop(self):
        self._running = False
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()