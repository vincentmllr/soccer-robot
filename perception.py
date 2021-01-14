import os
import time
import math
import io

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

import environment

SERIAL = "008014c1"
MODEL_FILENAME = 'model_s1.pb'
LABELS_FILENAME = 'labels.txt'
FOCALLENGTH = 14.86
rotation_to_ball = None


# Klasse zur Bildverarbeitung online
class VideoProcessingCloud():

    # Verbindungsdaten laden
    def __init__(self):

        self.ENDPOINT = "https://vector.cognitiveservices.azure.com/"
        self.prediction_key = "a9f0177e6df54a63a7d6cc9477c383f9"
        self.prediction_resource_id = "/subscriptions/f6e54442-3d5a-4083-ad0d-080f159ac33d/resourceGroups/Vision/providers/Microsoft.CognitiveServices/accounts/Vector"
        self.project_id = "d2693bf6-e18a-414f-bdba-2851847b43a0"
        self.publish_iteration_name = "Iteration6"

        self.prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": self.prediction_key})
        self.predictor = CustomVisionPredictionClient(self.ENDPOINT, self.prediction_credentials)

        self.running = True

    # Bild verarbeiten
    def detection(self, robot, env):
        # Fenster wird erstellt
        window_name = "Enemy Detection"
        cv.namedWindow(window_name, cv.WINDOW_NORMAL)
        cv.resizeWindow(window_name, 500, 490)

        while robot.camera.image_streaming_enabled():
            # Bild wird aufgenommen und vorbereitet
            t = time.time()
            image = robot.camera.latest_image.raw_image
            width, height = image.size
            byte_image = take_picture_to_byte(image)
            frame = cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)

            # Bild wird an Server gesendet
            prediction_results = self.predictor.detect_image(self.project_id, self.publish_iteration_name, byte_image)
            elapsed = time.time()-t

            found_vector = False

            # Anzeigen der Ergebnisse
            for prediction in prediction_results.predictions:
                if prediction.probability > 0.2:
                    print("\t" + prediction.tag_name + ": {0:.2f}% bbox.left = {1:.2f}, bbox.top = {2:.2f}, bbox.width = {3:.2f}, bbox.height = {4:.2f}".format(
                        prediction.probability * 100, prediction.bounding_box.left, prediction.bounding_box.top, prediction.bounding_box.width, prediction.bounding_box.height))

                # Filtern der Ergebnisse
                if prediction.tag_name == 'Vector' and found_vector == False:
                    if prediction.probability > 0.4:

                        # Eckpunkte des Rechteck bestimmen
                        # Rechteck zeichnen
                        ol = (prediction.bounding_box.left * width,prediction.bounding_box.top * height)
                        ur = ((prediction.bounding_box.left + prediction.bounding_box.width) * width, (width,prediction.bounding_box.top - prediction.bounding_box.height) * height)
                        color = (0, 0, 255)
                        cv.rectangle(frame, ol, ur, color)

                        # Berechnen der Position des Gegners
                        estimated_distance = (650*FOCALLENGTH)/(prediction.bounding_box.height * height)
                        estimated_rotation_to_enemy = (0.5-(prediction.bounding_box.left + 0.5 * prediction.bounding_box.width)) * -90
                        rotation_sum = env._self.rotation + estimated_rotation_to_enemy

                        estimated_x = env.self.position_x + (math.cos(rotation_sum) * estimated_distance)
                        estimated_y = env.self.position_y + (math.sin(rotation_sum) * estimated_distance)

                        # Hinzufügen zu Environment
                        env.enemy.position_x = estimated_x
                        env.enemy.position_y = estimated_y
                        env.enemy._last_seen = t

                        found_vector = True

                # Anzeige des Bildes mit Ergebnis
                cv.imshow(window_name, frame)

                # q Drücken zum schließen
                key = cv.waitKey(10)
                if key == ord('q') or key == 27:
                    break


# Offline Bildverarbeitung mit TensorFlow
class VideoProcessingTF():

    INPUT_TENSOR_NAME = 'image_tensor:0'
    OUTPUT_TENSOR_NAMES = ['detected_boxes:0', 'detected_scores:0', 'detected_classes:0']

    # Laden des Models
    def __init__(self, model_filename):
        graph_def = tf.compat.v1.GraphDef()
        with open(model_filename, 'rb') as f:
            graph_def.ParseFromString(f.read())

        self.graph = tf.Graph()
        with self.graph.as_default():
            tf.import_graph_def(graph_def, name='')

        with tf.compat.v1.Session(graph=self.graph) as sess:
            self.input_shape = sess.graph.get_tensor_by_name(self.INPUT_TENSOR_NAME).shape.as_list()[1:3]

    # Methode zu Verarbeitung der Bilddaten von Vektor
    def detection(self, robot, env):
        window_name = "Enemy Detection"
        cv.namedWindow(window_name, cv.WINDOW_NORMAL)
        cv.resizeWindow(window_name, 500, 490)

        while robot.camera.image_streaming_enabled():
            # Aufnehmen des Bildes und Umwandlung in verschiedene Formate
            t = time.time()
            image = robot.camera.latest_image.raw_image
            width, height = image.size
            frame = cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)
            image = image.convert('RGB') if image.mode != 'RGB' else image
            image = image.resize(self.input_shape)

            # Bild wird verarbeitet
            inputs = np.array(image, dtype=np.float32)[np.newaxis, :, :, :]
            with tf.compat.v1.Session(graph=self.graph) as sess:
                output_tensors = [sess.graph.get_tensor_by_name(n) for n in self.OUTPUT_TENSOR_NAMES]
                outputs = sess.run(output_tensors, {self.INPUT_TENSOR_NAME: inputs})
                elapsed = time.time() - t
                print("Duration: ", elapsed)

                # Ergebnisliste wird zerlegt
                result_array = outputs.pop(0)
                probability_array = outputs.pop(0)

                if probability_array[0] > 0.6:

                    # Eckpunkte des Rechteck bestimmen
                    # Rechteck zeichnen
                    result = result_array[0]
                    ol = (int(result[0] * width), int(result[1] * height))
                    ur = (int(result[2] * width), int(result[3] * height))
                    color = (0, 0, 255)
                    cv.rectangle(frame, ol, ur, color)

                    # Berechnen der Position des Gegners
                    enemy_width = (result[0] - result[2])
                    enemy_height = (result[1] - result[3])
                    estimated_distance = (650*FOCALLENGTH)/(enemy_height * height)
                    estimated_rotation_to_enemy = (0.5-(result[0] + 0.5 * enemy_width)) * -90
                    rotation_sum = env.self.rotation + estimated_rotation_to_enemy

                    estimated_x = env.self.position_x + (math.cos(rotation_sum) * estimated_distance)
                    estimated_y = env.self.position_y + (math.sin(rotation_sum) * estimated_distance)

                    # Hinzufügen zum Environment
                    env.enemy.position_x = estimated_x
                    env.enemy.position_y = estimated_y
                    env.enemy._last_seen = t

                # Bild mit Rechteck anzeigen
                cv.imshow(window_name, frame)

                # q Drücken zum schließen    
                key = cv.waitKey(10)
                if key == ord('q') or key == 27:
                    break    
            

class MaskWindow():
    def __init__(self, window_name, low_H, low_S, low_V, high_H, high_S, high_V, is_master):
        self.window_name = window_name
        self.low_H = low_H
        self.low_S = low_S
        self.low_V = low_V
        self.high_H = high_H
        self.high_S = high_S
        self.high_V = high_V
        self.max_value_H = 360//2
        self.max_value = 255
        self.low_H_name = 'Low H'
        self.low_S_name = 'Low S'
        self.low_V_name = 'Low V'
        self.high_H_name = 'High H'
        self.high_S_name = 'High S'
        self.high_V_name = 'High V'
        self.min_radius_name = 'Min Radius'
        self.min_radius = 10
        self.is_master = is_master
        
        
    def get_values(self):
        return (self.low_H, self.low_S, self.low_V), (self.high_H, self.high_S, self.high_V)
    
    def preprocess(self, frame_HSV):
        frame_threshold = cv.inRange(frame_HSV, (self.low_H, self.low_S, self.low_V), (self.high_H, self.high_S, self.high_V))
        frame_threshold = cv.erode(frame_threshold, None, iterations=2)
        frame_threshold = cv.dilate(frame_threshold, None, iterations=2)
        return frame_threshold

    def calculate_rotation(self, goal_rotation, dist, x, y, left_angle, right_angle, gamma, width):
        rotation_to_z = None
        if right_angle > 90:
            rotation_to_z = goal_rotation + 90 - left_angle + (width/2 - x) - (gamma/2)
        if right_angle < 90:
            rotation_to_z = goal_rotation - 90 + left_angle + (width/2 - x) - (gamma/2)
    
    def round_to_interval(self, val):
        val = max(val, -1)
        val = min(val, 1)
        return val

    def find_ball(self, env, frame_threshold, frame, min_radius):
        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        cnts = cv.findContours(frame_threshold.copy(), cv.RETR_EXTERNAL,
            cv.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        center = None

        # only proceed if at least one contour was found
        if len(cnts) > 0:

            # Größte Kontur finden
            c = max(cnts, key=cv.contourArea)
            ((x, y), radius) = cv.minEnclosingCircle(c)
            M = cv.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            if radius > min_radius:
                # Kreis malen
                cv.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv.circle(frame, center, 5, (0, 0, 255), -1)

                # Ball zu environment hinzufügen
                # Distance = real radius * focallength / radius in the frame
                global rotation_to_ball
                
                estimated_distance = (400*FOCALLENGTH)/radius
                estimated_rotation_to_ball = (-0.5 + (x/620)) * -90

                rotation_to_ball = estimated_rotation_to_ball
                rotation_sum = env.self.rotation + estimated_rotation_to_ball
                estimated_x = env.self.position_x + (math.cos(rotation_sum) * estimated_distance)
                estimated_y = env.self.position_y + (math.sin(rotation_sum) * estimated_distance)

                env.ball.position_x = estimated_x
                env.ball.position_y = estimated_y
                # env.ball._last_seen = timestamp
                env.self.angle_to_ball = rotation_to_ball

            else:
                rotation_to_ball = None
                env.self.angle_to_ball = None

    def find_goal(self, env, frame_threshold, frame, width, goal_rotation):

        cnts = cv.findContours(frame_threshold.copy(), cv.RETR_EXTERNAL,
            cv.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        center1 = None
        center2 = None

        # Nur weiter machen wenn min zwei Konturen gefunden wurden
        if len(cnts) > 1:

            # finde die zwei größten Kreise
            max_area = -1
            second_max_area = -1
            c1 = None
            c2 = None
            for i in range(len(cnts)):
                area = cv.contourArea(cnts[i])
                if area > max_area and second_max_area <= max_area:
                    c2 = c1
                    c1 = cnts[i]
                    second_max_area = max_area
                    max_area = area
                elif area > second_max_area:
                    c2 = cnts[i]
                    second_max_area = area

            ((x1, y1), radius1) = cv.minEnclosingCircle(c1)
            M1 = cv.moments(c1)
            center1 = (int(M1["m10"] / M1["m00"]), int(M1["m01"] / M1["m00"]))
            ((x2, y2), radius2) = cv.minEnclosingCircle(c2)
            M2 = cv.moments(c2)
            center2 = (int(M2["m10"] / M2["m00"]), int(M2["m01"] / M2["m00"]))

            # Der linke Kreis ist immer Nummer 1
            if x1 > x2:
                x3, y3, radius3, M3 = x2, y2, radius2, M2
                x2, y2, radius2, M2 = x1, y1, radius1, M1
                x1, y1, radius1, M1 = x3, y3, radius3, M3

            # Nur weiter machen bei einer Mindestgröße
            if radius1 > 10 and radius2 > 10:

                cv.circle(frame, (int(x1), int(y1)), int(radius1),
                    (255, 0, 0), 2)
                cv.circle(frame, center1, 5, (0, 0, 255), -1)
                
                cv.circle(frame, (int(x2), int(y2)), int(radius2),
                    (255, 255, 0), 2)
                cv.circle(frame, center2, 5, (0, 0, 255), -1)

                # Distanzberechnung mit ausgleich für die Höhe
                dist_a = (400*FOCALLENGTH)/radius1
                dist_b = (400*FOCALLENGTH)/radius2
                dist_a = math.sqrt(math.pow(dist_a, 2) - 49)
                dist_b = math.sqrt(math.pow(dist_b, 2) - 49)
                dist_c = 200


                # Winkel aus Dreieck mit Markerpunkten und Kamera
                pre_alpha = ((dist_a ** 2) - (dist_b ** 2) - (dist_c ** 2)) / (-2 * dist_b * dist_c)
                alpha = math.acos(self.round_to_interval(pre_alpha))
                pre_beta = ((dist_b ** 2) - (dist_a ** 2) - (dist_c ** 2)) / (-2 * dist_a * dist_c)
                beta = math.acos(self.round_to_interval(pre_beta))
                delta = 180 - beta
                epsilon = 180 - alpha

                if goal_rotation == 180:
                    goal_x = x1 + ((x2 - x1)/2)
                    rotation_to_goal = (goal_x - 320)/640 * -90
                    env.self.angle_to_goal_self = rotation_to_goal
                    if dist_a < dist_b:
                        x_self = (math.sin(delta) * dist_a) 
                        if beta > 90:
                            y_self = 400 - (math.cos(delta) * dist_a)
                        elif beta < 90:
                            y_self = 400 + (math.cos(beta) * dist_a)
                    elif dist_b < dist_a:
                        x_self = (math.sin(epsilon) * dist_b)
                        if alpha > 90:
                            y_self = 600 + (math.cos(delta) * dist_b)
                        elif alpha < 90:
                            y_self = 600 - (math.cos(beta) * dist_b)

                elif goal_rotation == 0:
                    goal_x = x1 + ((x2 - x1)/2)
                    rotation_to_goal = (goal_x - 320)/640 * -90
                    env.self.angle_to_goal_enemy = rotation_to_goal
                    if dist_a < dist_b:
                        x_self = 1600 - (math.sin(delta) * dist_a)
                        if beta > 90:
                            y_self = 600 + (math.cos(delta) * dist_a)
                        elif beta < 90:
                            y_self = 600 - (math.cos(beta) * dist_a)
                    elif dist_b < dist_a:
                        x_self = 1600 - (math.sin(epsilon) * dist_b)
                        if alpha > 90:
                            y_self = 400 - (math.cos(delta) * dist_b)
                        elif alpha < 90:
                            y_self = 400 + (math.cos(beta) * dist_b)   
                


                #env._self.position_x(x_self)
                #env._self.position_y(y_self)
                #env._self.rotation(vector_rotation)

    def build_window(self):

        if self.is_master == False:

            def on_low_H_thresh_trackbar(val):
                self.low_H = val
                self.low_H = min(self.high_H-1, self.low_H)
                cv.setTrackbarPos(self.low_H_name, self.window_name, self.low_H)

            def on_high_H_thresh_trackbar(val):
                self.high_H = val
                self.high_H = max(self.high_H, self.low_H+1)
                cv.setTrackbarPos(self.high_H_name, self.window_name, self.high_H)

            def on_low_S_thresh_trackbar(val):
                self.low_S = val
                self.low_S = min(self.high_S-1, self.low_S)
                cv.setTrackbarPos(self.low_S_name, self.window_name, self.low_S)

            def on_high_S_thresh_trackbar(val):
                self.high_S = val
                self.high_S = max(self.high_S, self.low_S+1)
                cv.setTrackbarPos(self.high_S_name, self.window_name, self.high_S)

            def on_low_V_thresh_trackbar(val):
                self.low_V = val
                self.low_V = min(self.high_V-1, self.low_V)
                cv.setTrackbarPos(self.low_V_name, self.window_name, self.low_V)

            def on_high_V_thresh_trackbar(val):
                self.high_V = val
                self.high_V = max(self.high_V, self.low_V+1)
                cv.setTrackbarPos(self.high_V_name, self.window_name, self.high_V)

            def on_high_V_thresh_trackbar(val):
                self.min_radius = val
                self.high_V = max(self.high_V, self.low_V+1)
                cv.setTrackbarPos(self.high_V_name, self.window_name, self.high_V)

            def radius_trackbar(val):
                self.min_radius = val
                cv.setTrackbarPos(self.min_radius_name, self.window_name, self.high_V)

            cv.createTrackbar(self.low_H_name, self.window_name, self.low_H, self.max_value_H, on_low_H_thresh_trackbar)
            cv.createTrackbar(self.high_H_name, self.window_name, self.high_H, self.max_value_H, on_high_H_thresh_trackbar)
            cv.createTrackbar(self.low_S_name, self.window_name, self.low_S, self.max_value, on_low_S_thresh_trackbar)
            cv.createTrackbar(self.high_S_name, self.window_name, self.high_S, self.max_value, on_high_S_thresh_trackbar)
            cv.createTrackbar(self.low_V_name, self.window_name, self.low_V, self.max_value, on_low_V_thresh_trackbar)
            cv.createTrackbar(self.high_V_name, self.window_name, self.high_V, self.max_value, on_high_V_thresh_trackbar)

            if self.window_name == "Ball Detection":
                cv.createTrackbar(self.min_radius_name, self.window_name, 0, 40, radius_trackbar)

        elif self.is_master == True:

            def trackbar_camera(val):
                global show_window_camera
                show_window_camera = val

            def trackbar_ball(val):
                global show_window_ball
                show_window_ball = val

            def trackbar_goal_self(val):
                global show_window_goal_self
                show_window_goal_self = val

            def trackbar_goal_enemy(val):
                global show_window_goal_enemy
                show_window_goal_enemy = val

            cv.createTrackbar("Vector Camera", self.window_name, 0, 1, trackbar_camera)
            cv.createTrackbar("Ball Detection", self.window_name, 0, 1, trackbar_ball)
            cv.createTrackbar("Goal Self", self.window_name, 0, 1, trackbar_goal_self)
            cv.createTrackbar("Goal Enemy", self.window_name, 0, 1, trackbar_goal_enemy)


# init_camera_feed muss davor ausführen
# Klasse für einfache geometrische Ballerkennung
class VideoProcessingOpenCV():

    def __init__(self):
        self.window_capture_name = 'Vectors Camera'
        self.window_detection_name_ball = 'Ball Detection'
        self.window_detection_name_goal_self = 'Goal Self'
        self.window_detection_name_goal_enemy = 'Goal Enemy'
        self.window_master_name = "Master"

    def start_tracking(self, robot, env):

        # Windows erstellen
        cv.namedWindow(self.window_capture_name, cv.WINDOW_NORMAL)
        cv.namedWindow(self.window_detection_name_ball, cv.WINDOW_NORMAL)
        cv.namedWindow(self.window_detection_name_goal_self, cv.WINDOW_NORMAL)
        cv.namedWindow(self.window_master_name, cv.WINDOW_NORMAL)

        exist_camera = True
        exist_ball =  True
        exist_goal =  True
        exist_goal_enemy =  True

        cv.moveWindow(self.window_capture_name, 0, -100)
        cv.moveWindow(self.window_detection_name_ball, 550, -1)
        cv.moveWindow(self.window_detection_name_goal_self, 0, 230)
        cv.moveWindow(self.window_master_name, 700, 0)

        master_trackbar = MaskWindow(self.window_master_name, 0, 0, 0, 0, 0, 0, True)
        master_trackbar.build_window()

        mask_ball = MaskWindow(self.window_detection_name_ball, 6, 104, 140, 60, 242, 195, False)
        mask_ball.build_window()

        mask_goal = MaskWindow(self.window_detection_name_goal_self, 80, 130, 50, 180, 242, 195, False)
        mask_goal.build_window()

        mask_goal_enemy = MaskWindow(self.window_detection_name_goal_enemy, 110, 130, 50, 180, 242, 195, False)
        mask_goal_enemy.build_window()

        while robot.camera.image_streaming_enabled():

            timestamp = time.time()
            img = robot.camera.latest_image.raw_image
            frame = cv.cvtColor(np.array(img), cv.COLOR_RGB2BGR)
            width = img.width

            if frame is None:
                break
            width = 620
            frame_HSV = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

            # Maske erstellen
            frame_threshold_ball = mask_ball.preprocess(frame_HSV)
            frame_threshold_goal_self = mask_goal.preprocess(frame_HSV)
            frame_threshold_goal_enemy = mask_goal_enemy.preprocess(frame_HSV)

            min_radius = cv.getTrackbarPos("Minimum Radius", self.window_detection_name_ball)
            mask_ball.find_ball(env, frame_threshold_ball, frame, min_radius)
            mask_goal.find_goal(env, frame_threshold_goal_self, frame, width, 180)
            # mask_goal_enemy.find_goal(env, frame_threshold_goal_self, frame, width, 0)

            cv.resizeWindow(self.window_capture_name, 550, 320)
            cv.resizeWindow(self.window_detection_name_ball, 550, 350)
            cv.resizeWindow(self.window_detection_name_goal_self, 550, 350)

            show_window_camera = cv.getTrackbarPos("Vector Camera", self.window_master_name)
            show_window_ball = cv.getTrackbarPos("Ball Detection", self.window_master_name)
            show_window_goal_self = cv.getTrackbarPos("Goal Self", self.window_master_name)
            show_window_goal_enemy = cv.getTrackbarPos("Goal Enemy", self.window_master_name)

            if show_window_camera == 1 and exist_camera == True:
                cv.imshow(self.window_capture_name, frame)
            elif show_window_camera == 1 and exist_camera == False:
                cv.namedWindow(self.window_capture_name, cv.WINDOW_NORMAL)
                mask_ball.build_window()
                cv.moveWindow(self.window_capture_name, 0, -100)
                exist_camera = True
                cv.imshow(self.window_capture_name, frame)
            elif show_window_camera == 0 and exist_camera == True:
                cv.destroyWindow(self.window_capture_name)
                exist_camera = False

            if show_window_ball == 1 and exist_ball == True:
                cv.imshow(self.window_detection_name_ball, frame_threshold_ball)
            elif show_window_ball == 1 and exist_ball == False:
                cv.namedWindow(self.window_detection_name_ball, cv.WINDOW_NORMAL)
                mask_ball.build_window()
                cv.moveWindow(self.window_detection_name_ball, 0, -100)
                exist_ball = True
                cv.imshow(self.window_detection_name_ball, frame_threshold_ball)
            elif show_window_ball == 0 and exist_ball == True:
                cv.destroyWindow(self.window_detection_name_ball)
                exist_ball = False

            if show_window_goal_self == 1 and exist_goal == True:
                cv.imshow(self.window_detection_name_goal_self, frame_threshold_goal_self)
            elif show_window_goal_self == 1 and exist_goal == False:
                cv.namedWindow(self.window_detection_name_goal_self, cv.WINDOW_NORMAL)
                mask_goal.build_window()
                cv.moveWindow(self.window_detection_name_goal_self, 0, -100)
                exist_goal = True
                cv.imshow(self.window_detection_name_goal_self, frame_threshold_goal_self)
            elif show_window_goal_self == 0 and exist_goal == True:
                cv.destroyWindow(self.window_detection_name_goal_self)
                exist_goal = False

            if show_window_goal_enemy == 1 and exist_goal_enemy == True:
                cv.imshow(self.window_detection_name_goal_enemy, frame_threshold_goal_enemy)
            elif show_window_goal_enemy == 1 and exist_goal_enemy == False:
                cv.namedWindow(self.window_detection_name_goal_enemy, cv.WINDOW_NORMAL)
                mask_goal.build_window()
                cv.moveWindow(self.window_detection_name_goal_enemy, 0, -100)
                exist_goal_enemy = True
                cv.imshow(self.window_detection_name_goal_enemy, frame_threshold_goal_enemy)
            elif show_window_goal_enemy == 0 and exist_goal_enemy == True:
                cv.destroyWindow(self.window_detection_name_goal_enemy)
                exist_goal_enemy = False

            # q Drücken zum schließen
            key = cv.waitKey(30)
            if key == ord('q') or key == 27:
                break

# Aktiviert Offline oder Online Erkennung von Gegner
def detect_enemy(robot, env, mode):
    if robot.camera.image_streaming_enabled() is False:
        robot.camera.init_camera_feed()

    if mode == "online":
        videoprocessor = VideoProcessingCloud()
        videoprocessor.detection(robot, env)

    elif mode == "offline":
        videoprocessor = VideoProcessingTF(MODEL_FILENAME)
        videoprocessor.detection(robot, env)


# Aktivieren der Ball und Markererkennung
def detect_openCV(robot, env):
    robot.camera.init_camera_feed()
    bt = VideoProcessingOpenCV()
    bt.start_tracking(robot, env)

# Hilfsfunktion um Bild in Bytestrom umzuwandeln
def take_picture_to_byte(image):

    with io.BytesIO() as output:
        image.save(output, 'BMP')
        image_as_bytes = output.getvalue()

    return image_as_bytes

# Winkel zwischen Vector und Ball zurückgeben
def current_rotation_to_ball():
    return rotation_to_ball 

def test_perception():

    def start_robot():
        robot = anki_vector.Robot(serial=SERIAL)
        env = environment.Environment(robot,
                                field_length_x=2000.0,
                                field_length_y=1000.0,
                                goal_width=200.0,
                                ball_diameter=40.0,
                                position_start_x=100.0,
                                position_start_y=500.0,
                                enable_environment_viewer=False)
        robot.connect()
        robot.camera.init_camera_feed()
        robot.behavior.set_eye_color(0.05, 1.0)
        robot.behavior.set_head_angle(degrees(0))
        return (robot, env)

    print("Für einen Test der Perception ohne Vector bitte die Testversion im Ordner Test Code nutzen")
    modus = None
    while modus is None:
        print("Drücke für offline Bildererkennung (1), online Bilderkennung (2), offline Ballerkennung (3), Abrruch (4)")
        modus = input()
        if modus == "1":
            robot, env = start_robot()
            detect_object(robot, env, "offline")  
        elif modus == "2":
            robot, env = start_robot()
            detect_object(robot, env, "online")  
        elif modus == "3":
            robot, env = start_robot()
            detect_openCV(robot, env)
        elif modus == "4":
            break
        else:
            modus = None




if __name__ == "__main__":
    test_perception()
