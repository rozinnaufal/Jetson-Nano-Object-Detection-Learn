from flask import Flask, render_template, Response

import cv2
import json 
import numpy as np

from utils import Utils

utils = Utils()

classesFile = "coco.json"
with open(classesFile) as json_labels:
    classes = json.load(json_labels)

# parameter
target_w = 244
target_h = 244

# load petrained model (.pb & .pbtxt) faster R-CNN with backbone Resnet 50 on COCO dataset
net = cv2.dnn.readNetFromTensorflow("model/faster_rcnn_frozen_inference_graph.pb", 
                                    "model/faster_rcnn_resnet50_coco_2018_01_28.pbtxt")

# set CUDA as backend & target OpenCV DNN
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

# get output layers
layerOutput = net.getUnconnectedOutLayersNames()
print(net.getLayerNames(), layerOutput)

app = Flask(__name__)

camera = cv2.VideoCapture(0)

def detect_object(frame):
    frame = frame[:, 80:-80]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (target_w, target_h), (0, 0, 0), swapRB=True, crop=False)

    # predict classess & box
    net.setInput(blob)
    output = net.forward(layerOutput)
    
    t, _ = net.getPerfProfile()
    print('inference time: %.2f s' % (t / cv2.getTickFrequency()))

    return utils.postprocess(output, frame, classes, font_size=0.8)

def gen_frames():  
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame  = detect_object(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

app.run(host="0.0.0.0")
