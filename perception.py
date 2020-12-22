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
                    environment._enemy._position_x = estimated_x
                    environment._enemy._position_x = estimated_y
                    environment._enemy._last_seen = picture_timestamp
                    found_ball = True
                    print("Vector detected. Estimated position: " + estimated_x + ", " + estimated_y + ". Timestamp: " + picture_timestamp)
                    

            if prediciton.tag_name == 'Ball' and found_ball == False:
                if prediction.probability > 0.4:
                    estimated_distance = prediction.bounding_box.height * 30.00391
                    if estimated_distance < 100 or  prediction.bounding_box.height + 0.1 < prediction.bounding_box.width:
                        object_distance = distance(robot)
                        if object_distance is not None:
                            estimated_distance = object_distance
                    estimated_x = robot.position.x + (math.cos(robot.rotation.q0) * estimated_distance)
                    estimated_y = robot.position.y + (math.sin(robot.rotation.q0) * estimated_distance)
                    environment._ball._position_x = estimated_x
                    environment._ball._position_x = estimated_y
                    environment._ball._last_seen = picture_timestamp
                    found_ball = True
                    print("Ball detected. Estimated position: " + estimated_x + ", " + estimated_y + ". Timestamp: " + picture_timestamp)

            if counter >= 4:
                break


# Predictionclass for offline prediction with Tensorflow
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

  


def detect_object(robot, mode, environment):
    if mode == "online":
        predictor = PredictionCloud()
        t = time.time()
        image = sf.take_picture_to_byte(robot)
        result = predictor.prediction(image ,t, environment)
        elapsed = time.time() - t
        print('Duration:', elapsed)
        return result
    else:
        
        t = time.time()
        od_model = PredictionTF(model_filename)
        image = robot.camera.latest_image.raw_image()
        image = PIL.Image.open(image_filename, t, environment)
        result = od_model.predict_image(image)
        elapsed = time.time() - t
        print("Duration: ", elapsed)


