import os
import time

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateEntry, Region
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials

from PIL import Image
import PIL.Image

import argparse
import tensorflow as tf
import numpy as np

from collections import deque
from imutils.video import VideoStream
import cv2 as cv
import imutils

import environment



MODEL_FILENAME = 'model_s1.pb'
LABELS_FILENAME = 'labels.txt'


# Predictionclass for online prediction with Azure Custom Vision
class PredictionCloud():


    def __init__(self):

        self.ENDPOINT = "https://vector.cognitiveservices.azure.com/"
        self.prediction_key = "a9f0177e6df54a63a7d6cc9477c383f9"
        self.prediction_resource_id = "/subscriptions/f6e54442-3d5a-4083-ad0d-080f159ac33d/resourceGroups/Vision/providers/Microsoft.CognitiveServices/accounts/Vector"
        self.project_id = "d2693bf6-e18a-414f-bdba-2851847b43a0"
        self.publish_iteration_name = "Iteration3"
        
        self.prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": self.prediction_key})
        self.predictor = CustomVisionPredictionClient(self.ENDPOINT, self.prediction_credentials)

        
    def prediction(self, image, picture_timestamp, environment):
        
        prediction_results = self.predictor.detect_image(self.project_id, self.publish_iteration_name, image)
        found_ball = False
        found_vector = False

        # Display the results.
        counter = 0
        for prediction in prediction_results.predictions:
            counter = counter + 1
            print("\t" + prediction.tag_name + ": {0:.2f}% bbox.left = {1:.2f}, bbox.top = {2:.2f}, bbox.width = {3:.2f}, bbox.height = {4:.2f}".format(
                prediction.probability * 100, prediction.bounding_box.left, prediction.bounding_box.top, prediction.bounding_box.width, prediction.bounding_box.height))
                
            # if prediction.probability > 0.4:
            #     return float(prediction.bounding_box.left + 0.5 * prediction.bounding_box.width)
           

            # TODO Anpassen der Abstandsschätzung

            if prediciton.tag_name == 'Vector' and found_vector == False:
                if prediction.probability > 0.4:
                    estimated_distance = prediction.bounding_box.height * 15
                    if estimated_distance < 100:
                        object_distance = distance(robot)
                        if object_distance is not None:
                            estimated_distance = object_distance
                    estimated_x = robot.position.x + (math.cos(robot.rotation.q0) * estimated_distance)
                    estimated_y = robot.position.y + (math.sin(robot.rotation.q0) * estimated_distance)
                    env._enemy._position_x = estimated_x
                    env._enemy._position_x = estimated_y
                    env._enemy._last_seen = picture_timestamp
                    found_ball = True
                    print("Vector detected. Estimated position: " + estimated_x + ", " + estimated_y + ". Timestamp: " + picture_timestamp)
                    

            if prediciton.tag_name == 'Ball' and found_ball == False:
                if prediction.probability > 0.4:
                    estimated_distance = (400*4.25)/prediction.bounding_box.height
                    if estimated_distance < 100 or  prediction.bounding_box.height + 0.1 < prediction.bounding_box.width:
                        object_distance = distance(robot)
                        if object_distance is not None:
                            estimated_distance = object_distance
                    estimated_x = robot.position.x + (math.cos(robot.rotation.q0) * estimated_distance)
                    estimated_y = robot.position.y + (math.sin(robot.rotation.q0) * estimated_distance)
                    env._ball._position_x = estimated_x
                    env._ball._position_x = estimated_y
                    env._ball._last_seen = picture_timestamp
                    found_ball = True
                    print("Ball detected. Estimated position: " + estimated_x + ", " + estimated_y + ". Timestamp: " + picture_timestamp)

            if counter >= 4:
                break


# Predictionclass for offline prediction with Tensorflow
#TODO Implementierung Environment
class PredictionTF():
    INPUT_TENSOR_NAME = 'image_tensor:0'
    OUTPUT_TENSOR_NAMES = ['detected_boxes:0', 'detected_scores:0', 'detected_classes:0']

    def __init__(self, model_filename):
        graph_def = tf.compat.v1.GraphDef()
        with open(model_filename, 'rb') as f:
            graph_def.ParseFromString(f.read())

        self.graph = tf.Graph()
        with self.graph.as_default():
            tf.import_graph_def(graph_def, name='')

        # Get input shape
        with tf.compat.v1.Session(graph=self.graph) as sess:
            self.input_shape = sess.graph.get_tensor_by_name(self.INPUT_TENSOR_NAME).shape.as_list()[1:3]

    def predict_image(self, image, picture_timestamp, environment):
        image = image.convert('RGB') if image.mode != 'RGB' else image
        image = image.resize(self.input_shape)

        inputs = np.array(image, dtype=np.float32)[np.newaxis, :, :, :]
        with tf.compat.v1.Session(graph=self.graph) as sess:
            output_tensors = [sess.graph.get_tensor_by_name(n) for n in self.OUTPUT_TENSOR_NAMES]
            outputs = sess.run(output_tensors, {self.INPUT_TENSOR_NAME: inputs})
            return outputs

class TrackBall():

    def start_tracking(self, robot, env):
        
        max_value = 255
        max_value_H = 360//2
        low_H = 0
        low_S = 174
        low_V = 189
        high_H = 26
        high_S = max_value
        high_V = max_value
        window_capture_name = 'Vectors Camera'
        window_detection_name = 'Object Detection'
        low_H_name = 'Low H'
        low_S_name = 'Low S'
        low_V_name = 'Low V'
        high_H_name = 'High H'
        high_S_name = 'High S'
        high_V_name = 'High V'


        def on_low_H_thresh_trackbar(val):
            global low_H
            global high_H
            low_H = val
            low_H = min(high_H-1, low_H)
            cv.setTrackbarPos(low_H_name, window_detection_name, low_H)
        def on_high_H_thresh_trackbar(val):
            global low_H
            global high_H
            high_H = val
            high_H = max(high_H, low_H+1)
            cv.setTrackbarPos(high_H_name, window_detection_name, high_H)
        def on_low_S_thresh_trackbar(val):
            global low_S
            global high_S
            low_S = val
            low_S = min(high_S-1, low_S)
            cv.setTrackbarPos(low_S_name, window_detection_name, low_S)
        def on_high_S_thresh_trackbar(val):
            global low_S
            global high_S
            high_S = val
            high_S = max(high_S, low_S+1)
            cv.setTrackbarPos(high_S_name, window_detection_name, high_S)
        def on_low_V_thresh_trackbar(val):
            global low_V
            global high_V
            low_V = val
            low_V = min(high_V-1, low_V)
            cv.setTrackbarPos(low_V_name, window_detection_name, low_V)
        def on_high_V_thresh_trackbar(val):
            global low_V
            global high_V
            high_V = val
            high_V = max(high_V, low_V+1)
            cv.setTrackbarPos(high_V_name, window_detection_name, high_V)
        
        parser = argparse.ArgumentParser(description='Code for Thresholding Operations using inRange tutorial.')
        parser.add_argument('--camera', help='Camera divide number.', default=0, type=int)
        args = parser.parse_args()
        #cap = cv.VideoCapture(args.camera)
        #cap = cv.VideoCapture(robot.camera.latest_image)
        cv.namedWindow(window_capture_name, cv.WINDOW_NORMAL)
        cv.namedWindow(window_detection_name, cv.WINDOW_NORMAL)
        cv.resizeWindow(window_detection_name, 500, 490)
        cv.resizeWindow(window_capture_name, 600, 480)


        cv.createTrackbar(low_H_name, window_detection_name , low_H, max_value_H, on_low_H_thresh_trackbar)
        cv.createTrackbar(high_H_name, window_detection_name , high_H, max_value_H, on_high_H_thresh_trackbar)
        cv.createTrackbar(low_S_name, window_detection_name , low_S, max_value, on_low_S_thresh_trackbar)
        cv.createTrackbar(high_S_name, window_detection_name , high_S, max_value, on_high_S_thresh_trackbar)
        cv.createTrackbar(low_V_name, window_detection_name , low_V, max_value, on_low_V_thresh_trackbar)
        cv.createTrackbar(high_V_name, window_detection_name , high_V, max_value, on_high_V_thresh_trackbar)


        while True:
            
            #ret, frame = cap.read()
            frame = cv.imread(robot.camera.latest_image)
            if frame is None:
                break
            timestamp = time.time()
            frame_HSV = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            frame_threshold = cv.inRange(frame_HSV, (low_H, low_S, low_V), (high_H, high_S, high_V))
            frame_threshold = cv.erode(frame_threshold, None, iterations=2)
            frame_threshold = cv.dilate(frame_threshold, None, iterations=2)

            # find contours in the mask and initialize the current
            # (x, y) center of the ball
            cnts = cv.findContours(frame_threshold.copy(), cv.RETR_EXTERNAL,
                cv.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            center = None

            # only proceed if at least one contour was found
            if len(cnts) > 0:
                # find the largest contour in the mask, then use
                # it to compute the minimum enclosing circle and
                # centroid
                c = max(cnts, key=cv.contourArea)
                ((x, y), radius) = cv.minEnclosingCircle(c)
                M = cv.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                # only proceed if the radius meets a minimum size
                if radius > 10:
                    # draw the circle and centroid on the frame,
                    # then update the list of tracked points
                    cv.circle(frame, (int(x), int(y)), int(radius),
                        (0, 255, 255), 2)
                    cv.circle(frame, center, 5, (0, 0, 255), -1)


                    #Add ball to environment
                    # Distance = real radius * focallength / radius in the frame
                    estimated_distance = (400*4.25)/radius
                    estimated_rotation_to_ball = (-0.5 + (x/1277.5)) * 90
                    rotation_sum = env._self.rotation + estimated_rotation_to_ball
                    estimated_x = env._self.position_x + (math.cos(rotation_sum) * estimated_distance)
                    estimated_y = env._self.position_y + (math.sin(rotation_sum) * estimated_distance)

                    env._ball._position_x = estimated_x
                    env._ball._position_x = estimated_y
                    env._ball._last_seen = timestamp



            
            
            cv.imshow(window_capture_name, frame)
            cv.imshow(window_detection_name, frame_threshold)
            
            key = cv.waitKey(30)
            if key == ord('q') or key == 27:
                break





def detect_object(robot, mode, environment):
    if mode == "online":
        predictor = PredictionCloud()
        t = time.time()
        image = sf.take_picture_to_byte(robot)
        result = predictor.prediction(image ,t, environment)
        elapsed = time.time() - t
        print('Duration:', elapsed)
        return result
    elif mode == "offline":
        t = time.time()
        od_model = PredictionTF(model_filename)
        image = robot.camera.latest_image.raw_image
        image = PIL.Image.open(image_filename, t, environment)
        result = od_model.predict_image(image)
        elapsed = time.time() - t
        print("Duration: ", elapsed)

def detect_ball(robot, environment):
    bt = TrackBall()
    bt.start_tracking(robot, environment)


if __name__ == "__main__":
    
    