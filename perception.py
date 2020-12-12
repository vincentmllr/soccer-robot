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


IMAGE_FILENAME = 'Ball14cm.png'
MODEL_FILENAME = 'model_s1.pb'
LABELS_FILENAME = 'labels.txt'


class PredictionCloud():


    def __init__(self):

        self.ENDPOINT = "https://vector.cognitiveservices.azure.com/"
        self.prediction_key = "a9f0177e6df54a63a7d6cc9477c383f9"
        self.prediction_resource_id = "/subscriptions/f6e54442-3d5a-4083-ad0d-080f159ac33d/resourceGroups/Vision/providers/Microsoft.CognitiveServices/accounts/Vector"
        self.project_id = "d2693bf6-e18a-414f-bdba-2851847b43a0"
        self.publish_iteration_name = "Iteration3"
        
        self.prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": self.prediction_key})
        self.predictor = CustomVisionPredictionClient(self.ENDPOINT, self.prediction_credentials)

        
    def prediction(self, image):
        
        prediction_results = self.predictor.detect_image(self.project_id, self.publish_iteration_name, image)

        # Display the results.
        for prediction in prediction_results.predictions:
            print("\t" + prediction.tag_name + ": {0:.2f}% bbox.left = {1:.2f}, bbox.top = {2:.2f}, bbox.width = {3:.2f}, bbox.height = {4:.2f}".format(
                prediction.probability * 100, prediction.bounding_box.left, prediction.bounding_box.top, prediction.bounding_box.width, prediction.bounding_box.height))
                
            if prediction.probability > 0.4:
                return float(prediction.bounding_box.left + 0.5 * prediction.bounding_box.width)
            #Add Field Objects onto the virtual map

            # Überlegung: Box Left + 0.5* width = Mittelpunkt des Balls

            # if prediciton.tag_name == 'Vector':
            #     if prediction.probability > 0.4:
            #         estimated_distance = 3 - prediction.bounding_box.height * 10
            #         if estimated_distance < 100:
            #             object_distance = distance(robot)
            #             if object_distance is not None:
            #                 estimated_distance = object_distance
            #         estimated_x = robot.position.x + (math.cos(robot.rotation.q0) * estimated_distance)
            #         estimated_y = robot.position.y + (math.sin(robot.rotation.q0) * estimated_distance)
            #         FO = field_object(ball, estimated_x, estimated_y, time.time())
            #         

            # if prediciton.tag_name == 'Ball':
            #     if prediction.probability > 0.4:
            #         estimated_distance = 3 - prediction.bounding_box.height * 10
            #         if estimated_distance < 100:
            #             object_distance = distance(robot)
            #             if object_distance is not None:
            #                 estimated_distance = object_distance
            #         estimated_x = robot.position.x + (math.cos(robot.rotation.q0) * estimated_distance)
            #         estimated_y = robot.position.y + (math.sin(robot.rotation.q0) * estimated_distance)
            #         FO = field_object(ball, estimated_x, estimated_y, time.time())

class ObjectDetection:
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

    def predict_image(self, image):
        image = image.convert('RGB') if image.mode != 'RGB' else image
        image = image.resize(self.input_shape)

        inputs = np.array(image, dtype=np.float32)[np.newaxis, :, :, :]
        with tf.compat.v1.Session(graph=self.graph) as sess:
            output_tensors = [sess.graph.get_tensor_by_name(n) for n in self.OUTPUT_TENSOR_NAMES]
            outputs = sess.run(output_tensors, {self.INPUT_TENSOR_NAME: inputs})
            return outputs


def predict_offline(model_filename, image_filename):
    print("Image Filename", image_filename)
    od_model = ObjectDetection(model_filename)

    image = PIL.Image.open(image_filename)
    return od_model.predict_image(image)
  

#Class to define an object on the map with the name, coordinates and timestamp of the predicted picture

def detect_object(robot, mode, image_filename):
    if mode == "online":
        predictor = PredictionCloud()
        t = time.time()
        result = predictor.prediction(image_filename)
        elapsed = time.time() - t
        print('Duration:', elapsed)
        return result
    else:
        t = time.time()
        predictions = predict_offline(MODEL_FILENAME, image_filename)
        elapsed = time.time() - t
        print("Duration: ", elapsed)


