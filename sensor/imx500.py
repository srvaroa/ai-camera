# This code is broadly based on the reference implementation from the official
# picamera2 repository, at https://github.com/raspberrypi/picamera2/blob/bbd730d8bf5c2b67f793674400b3e7eff6a28dce/examples/imx500/imx500_object_detection_demo.py
# under the following licensing terms
#
# --
#
# BSD 2-Clause License
#
# Copyright (c) 2021, Raspberry Pi
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import sys
import time
import numpy as np
import cv2
from PIL import Image
from picamera2 import MappedArray, Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import NetworkIntrinsics, postprocess_nanodet_detection
from sensor import Sensor

class IMX500Sensor(Sensor):

    def __init__(self, fps, onEvent):
        super().__init__(fps, onEvent)
        self.fps = float(fps)
        self.running = False
        self.picam2 = None
        self.imx500 = None
        self.intrinsics = None
        self.last_detections = []

    def start(self):
        self.running = True
        self.imx500 = IMX500("/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")
        self.imx500.show_network_fw_progress_bar()
        self.intrinsics = self.imx500.network_intrinsics
        if not self.intrinsics:
            self.intrinsics = NetworkIntrinsics()
            self.intrinsics.task = "object detection"
        elif self.intrinsics.task != "object detection":
            print("Network is not an object detection task", file=sys.stderr)
            return

        self.picam2 = Picamera2(self.imx500.camera_num)
        config = self.picam2.create_preview_configuration(
            controls={"FrameRate": 2}, buffer_count=12)
        self.picam2.start(config, show_preview=False)

        if self.intrinsics.preserve_aspect_ratio:
            self.imx500.set_auto_aspect_ratio()

        self.picam2.pre_callback = self.draw_detections
        while self.running:
            self.last_detections = self.parse_detections(self.picam2.capture_metadata())
            if len(self.last_detections) > 0:
                for d in self.last_detections:
                    # print(str(d))
                    if int(d.category) == 0: # based on COCO
                        self._onEvent("person", d.image_array)
            # time.sleep(1 / self.fps)

    def stop(self):
        self.running = False
        if self.picam2:
            self.picam2.stop()

    def parse_detections(self, metadata):
        threshold = 0.55
        np_outputs = self.imx500.get_outputs(metadata, add_batch=True)
        image_array = self.picam2.capture_array()
        input_w, input_h = self.imx500.get_input_size()
        if np_outputs is None:
            return self.last_detections

        if self.intrinsics.postprocess == "nanodet":
            boxes, scores, classes = postprocess_nanodet_detection(
                outputs=np_outputs[0],
                conf=threshold,
                iou_thres=0.65,
                max_out_dets=10)[0]
            from picamera2.devices.imx500.postprocess import scale_boxes
            boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
        else:
            boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
            if self.intrinsics.bbox_normalization:
                boxes = boxes / input_h
            if self.intrinsics.bbox_order == "xy":
                boxes = boxes[:, [1, 0, 3, 2]]
            boxes = np.array_split(boxes, 4, axis=1)
            boxes = zip(*boxes)


        self.last_detections = [
            Detection(self.imx500, self.picam2, box, category, score, metadata, image_array)
            for box, score, category in zip(boxes, scores, classes)
            if score > threshold
        ]
        return self.last_detections

    def draw_detections(self, request, stream="main"):
        detections = self.last_detections
        if detections is None:
            return
        with MappedArray(request, stream) as m:
            for detection in detections:
                x, y, w, h = detection.box
                label = f"({detection.conf:.2f})"
                (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                text_x = x + 5
                text_y = y + 15
                overlay = m.array.copy()
                cv2.rectangle(overlay, (text_x, text_y - text_height), (text_x + text_width, text_y + baseline), (255, 255, 255), cv2.FILLED)
                alpha = 0.30
                cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)
                cv2.putText(m.array, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness=2)
            if self.intrinsics.preserve_aspect_ratio:
                b_x, b_y, b_w, b_h = self.imx500.get_roi_scaled(request)
                color = (0, 255, 0)
                cv2.putText(m.array, "ROI", (b_x + 5, b_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                cv2.rectangle(m.array, (b_x, b_y), (b_x + b_w, b_y + b_h), (255, 0, 0, 0))

class Detection:
    def __init__(self, imx500, picam2, coords, category, conf, metadata, image_array):
        self.category = category
        self.conf = conf
        self.image_array = image_array
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)
        self.label = f"{conf}"

    def __str__(self):
        return f"Detection for category {self.category} at {self.box} with {self.conf:.2f}"
