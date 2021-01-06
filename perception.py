import os
import time
import math

import anki_vector
from anki_vector.util import *
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
import cv2 as cv
import imutils

import environment as env
import support_functions as sp


MODEL_FILENAME = 'model_s1.pb'
LABELS_FILENAME = 'labels.txt'
rotation_to_ball = None


# Klasse zur Bildverarbeitung online
# TODO  anzeige der Ergebnissebilder

class VideoProcessingCloud():

    # Verbindungsdaten laden
    def __init__(self):

        self.ENDPOINT = "https://vector.cognitiveservices.azure.com/"
        self.prediction_key = "a9f0177e6df54a63a7d6cc9477c383f9"
        self.prediction_resource_id = "/subscriptions/f6e54442-3d5a-4083-ad0d-080f159ac33d/resourceGroups/Vision/providers/Microsoft.CognitiveServices/accounts/Vector"
        self.project_id = "d2693bf6-e18a-414f-bdba-2851847b43a0"
        self.publish_iteration_name = "Iteration3"
        
        self.prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": self.prediction_key})
        self.predictor = CustomVisionPredictionClient(self.ENDPOINT, self.prediction_credentials)

    # Bild an den Server zur Bildverarbeitung senden
    def detection(self, image, timestamp, environment):

        detection_results = self.predictor.detect_image(self.project_id, self.publish_iteration_name, image)
        found_ball = False
        found_vector = False

        # Display the results.
        for prediction in detection_results.predictions:
            print("\t" + prediction.tag_name + ": {0:.2f}% bbox.left = {1:.2f}, bbox.top = {2:.2f}, bbox.width = {3:.2f}, bbox.height = {4:.2f}".format(
                prediction.probability * 100, prediction.bounding_box.left, prediction.bounding_box.top, prediction.bounding_box.width, prediction.bounding_box.height))

            # TODO Anpassen der Abstandsschätzung
            if prediciton.tag_name == 'Vector' and found_vector == False:
                if prediction.probability > 0.4:
                    estimated_distance = (650*14.86)/prediction.bounding_box.height

                    estimated_rotation_to_ball = (0.5-(prediction.bounding_box.left + 0.5 * prediction.bounding_box.width)) * -90
                    rotation_sum = env.self.rotation + estimated_rotation_to_ball

                    estimated_x = env.self.position_x + (math.cos(rotation_sum) * estimated_distance)
                    estimated_y = env.self.position_y + (math.sin(rotation_sum) * estimated_distance)

                    env.enemy.position_x = estimated_x
                    env.enemy.position_y = estimated_y
                    env.enemy._last_seen = timestamp

                    found_vector = True
                    print("Vector detected. Estimated position: " + estimated_x + ", " + estimated_y + ". Timestamp: " + picture_timestamp)


# Offline Bildverarbeitung mit TensorFlow
# TODO Implementierung Environment
class VideoProcessingTF():

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


# init_camera_feed muss davor ausführen
# Klasse für einfache geometrische Ballerkennung
class TrackBall():

    max_value = 255
    max_value_H = 360//2
    low_H = 6
    low_S = 145
    low_V = 140
    high_H = 60
    high_S = 255
    high_V = 245
    window_capture_name = 'Vectors Camera'
    window_detection_name = 'Object Detection'
    low_H_name = 'Low H'
    low_S_name = 'Low S'
    low_V_name = 'Low V'
    high_H_name = 'High H'
    high_S_name = 'High S'
    high_V_name = 'High V'

    def start_tracking(self, robot, env):

        def on_low_H_thresh_trackbar(val):
            global low_H
            global high_H
            self.low_H = val
            self.low_H = min(self.high_H-1, self.low_H)
            cv.setTrackbarPos(self.low_H_name, self.window_detection_name, self.low_H)

        def on_high_H_thresh_trackbar(val):
            global low_H
            global high_H
            self.high_H = val
            self.high_H = max(self.high_H, self.low_H+1)
            cv.setTrackbarPos(self.high_H_name, self.window_detection_name, self.high_H)

        def on_low_S_thresh_trackbar(val):
            global low_S
            global high_S
            self.low_S = val
            self.low_S = min(self.high_S-1, self.low_S)
            cv.setTrackbarPos(self.low_S_name, self.window_detection_name, self.low_S)

        def on_high_S_thresh_trackbar(val):
            global low_S
            global high_S
            self.high_S = val
            self.high_S = max(self.high_S, self.low_S+1)
            cv.setTrackbarPos(self.high_S_name, self.window_detection_name, self.high_S)

        def on_low_V_thresh_trackbar(val):
            global low_V
            global high_V
            self.low_V = val
            self.low_V = min(self.high_V-1, self.low_V)
            cv.setTrackbarPos(self.low_V_name, self.window_detection_name, self.low_V)

        def on_high_V_thresh_trackbar(val):
            global low_V
            global high_V
            self.high_V = val
            self.high_V = max(self.high_V, self.low_V+1)
            cv.setTrackbarPos(self.high_V_name, self.window_detection_name, self.high_V)

        # Windows erstellen
        cv.namedWindow(self.window_capture_name, cv.WINDOW_NORMAL)
        cv.namedWindow(self.window_detection_name, cv.WINDOW_NORMAL)
        cv.resizeWindow(self.window_detection_name, 500, 490)
        cv.resizeWindow(self.window_capture_name, 600, 550)

        # Trackbars für die Bildeinstellung hinzufügen
        cv.createTrackbar(self.low_H_name, self.window_detection_name , self.low_H, self.max_value_H, on_low_H_thresh_trackbar)
        cv.createTrackbar(self.high_H_name, self.window_detection_name , self.high_H, self.max_value_H, on_high_H_thresh_trackbar)
        cv.createTrackbar(self.low_S_name, self.window_detection_name , self.low_S, self.max_value, on_low_S_thresh_trackbar)
        cv.createTrackbar(self.high_S_name, self.window_detection_name , self.high_S, self.max_value, on_high_S_thresh_trackbar)
        cv.createTrackbar(self.low_V_name, self.window_detection_name , self.low_V, self.max_value, on_low_V_thresh_trackbar)
        cv.createTrackbar(self.high_V_name, self.window_detection_name , self.high_V, self.max_value, on_high_V_thresh_trackbar)

        while robot.camera.image_streaming_enabled():

            frame = cv.cvtColor(np.array(robot.camera.latest_image.raw_image), cv.COLOR_RGB2BGR)

            if frame is None:
                break

            timestamp = time.time()
            frame_HSV = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            frame_threshold = cv.inRange(frame_HSV, (self.low_H, self.low_S, self.low_V), (self.high_H, self.high_S, self.high_V))
            frame_threshold = cv.erode(frame_threshold, None, iterations=2)
            frame_threshold = cv.dilate(frame_threshold, None, iterations=2)

            # finde Kreise
            # (x, y) initialisieren
            cnts = cv.findContours(frame_threshold.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            center = None

            # Nur fortfahren, wenn mindestens ein Kreis gefunden wurde
            if len(cnts) > 0:

                # Größte Kontur finden
                c = max(cnts, key=cv.contourArea)
                ((x, y), radius) = cv.minEnclosingCircle(c)
                M = cv.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

                if radius > 10:
                    # Kreis malen
                    cv.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                    cv.circle(frame, center, 5, (0, 0, 255), -1)

                    # Ball zu environment hinzufügen
                    # Distance = real radius * focallength / radius in the frame
                    estimated_distance = (400*14.86)/radius
                    estimated_rotation_to_ball = (-0.5 + (x/620)) * -90
                    global rotation_to_ball = estimated_rotation_to_ball
                    rotation_sum = env.self.rotation + estimated_rotation_to_ball
                    estimated_x = env.self.position_x + (math.cos(rotation_sum) * estimated_distance)
                    estimated_y = env.self.position_y + (math.sin(rotation_sum) * estimated_distance)

                    env.ball.position_x = estimated_x
                    env.ball.position_y = estimated_y
                    env.ball._last_seen = timestamp

            # Frame in Fenster anzeigen
            cv.imshow(self.window_capture_name, frame)
            cv.imshow(self.window_detection_name, frame_threshold)

            # q Drücken zum schließen
            key = cv.waitKey(30)
            if key == ord('q') or key == 27:
                break


def detect_object(robot, environment, mode):

    if mode == "online":
        videoprocessor = VideoProcessingCloud()

        while True:
            t = time.time()
            image = robot.camera.latest_image.raw_image
            byte_image = take_picture_to_byte(image)
            videoprocessor.detection(byte_image, t, environment)
            elapsed = time.time() - t

            print('Duration:', elapsed)

    elif mode == "offline":
        od_model = VideoProcessingTF(MODEL_FILENAME)

        while True:
            t = time.time()
            image = robot.camera.latest_image.raw_image
            result = od_model.predict_image(image, t, environment)
            elapsed = time.time() - t

            print(result)
            print("Duration: ", elapsed)


# Aktivieren der Ballerkennung
def detect_ball(robot, environment):
    bt = TrackBall()
    bt.start_tracking(robot, environment)


# Hilfsfunktion um Bild in Bytestrom umzuwandeln
def take_picture_to_byte(image):

    with io.BytesIO() as output:
        image.save(output, 'BMP')
        image_as_bytes = output.getvalue()

    return image_as_bytes


# Winkel zwischen Vector und Ball zurückgeben
def current_rotation_to_ball():
    return rotation_to_ball


if __name__ == "__main__":
    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial) as robot:
        environment = env.Environment(robot,
                                    field_length_x=2000.0,
                                    field_length_y=1000.0,
                                    goal_width=200.0,
                                    ball_diameter=40.0,
                                    position_start_x=100.0,
                                    position_start_y=500.0,
                                    enable_environment_viewer=False)
        robot.camera.init_camera_feed()
        robot.behavior.set_eye_color(0.05, 1.0)
        robot.behavior.set_head_angle(degrees(0))
        # detect_object(robot, environment, "offline")

        detect_ball(robot, environment)
