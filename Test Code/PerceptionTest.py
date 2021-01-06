import os
import time
import math
import io


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
        self.publish_iteration_name = "Iteration6"

        self.prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": self.prediction_key})
        self.predictor = CustomVisionPredictionClient(self.ENDPOINT, self.prediction_credentials)

        self.running = True

    # Bild an den Server zur Bildverarbeitung senden
    def detection(self):
        window_name = "Enemy Detection"

        cv.namedWindow(window_name, cv.WINDOW_NORMAL)
        cv.resizeWindow(window_name, 500, 490)

        while self.running:
            t = time.time()
            image = Image.open("img1.jpg")
            byte_image = take_picture_to_byte(image)
            frame = cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)

            prediction_results = self.predictor.detect_image(self.project_id, self.publish_iteration_name, byte_image)
            elapsed = time.time()-t

            found_vector = False

            # Display the results.
            for prediction in prediction_results.predictions:
                if prediction.probability > 0.2:
                    print("\t" + prediction.tag_name + ": {0:.2f}% bbox.left = {1:.2f}, bbox.top = {2:.2f}, bbox.width = {3:.2f}, bbox.height = {4:.2f}".format(
                        prediction.probability * 100, prediction.bounding_box.left, prediction.bounding_box.top, prediction.bounding_box.width, prediction.bounding_box.height))

                # TODO Anpassen der Abstandsschätzung
                if prediction.tag_name == 'Vector' and found_vector == False:
                    if prediction.probability > 0.4:

                        width, height = image.size

                        ol = (int(prediction.bounding_box.left * width), int(prediction.bounding_box.top * height))
                        ur = (int((prediction.bounding_box.left + prediction.bounding_box.width) * width), int(max(0,(prediction.bounding_box.top + prediction.bounding_box.height)) * height))
                        color = (0, 0, 255)
                    
                        cv.rectangle(frame, ol, ur, color)

                        estimated_distance = (650*14.86)/prediction.bounding_box.height

                        estimated_rotation = (0.5-(prediction.bounding_box.left + 0.5 * prediction.bounding_box.width)) * -90
                        
                        estimated_x = (math.cos(estimated_rotation) * estimated_distance)
                        estimated_y = (math.sin(estimated_rotation) * estimated_distance)

                        # env.enemy.position_x = estimated_x
                        # env.enemy.position_y = estimated_y
                        # env.enemy._last_seen = timestamp

                        found_vector = True
                        print("Vector detected. Estimated position: " , estimated_x, ", ", estimated_y, ". Timestamp: ", t)

                        cv.imshow(window_name, frame)

                        key = cv.waitKey(30)
                        if key == ord('q') or key == 27:
                            break

    def stop():
        self.Running = False


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

    def predict_image(self):
        window_name = "Enemy Detection"
        cv.namedWindow(window_name, cv.WINDOW_NORMAL)
        cv.resizeWindow(window_name, 500, 490)

        while True:
            t = time.time()
            image = Image.open("img1.jpg")

            width, height = image.size
            frame = cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)
            image = image.convert('RGB') if image.mode != 'RGB' else image
            image = image.resize(self.input_shape)

            inputs = np.array(image, dtype=np.float32)[np.newaxis, :, :, :]
            with tf.compat.v1.Session(graph=self.graph) as sess:
                output_tensors = [sess.graph.get_tensor_by_name(n) for n in self.OUTPUT_TENSOR_NAMES]
                outputs = sess.run(output_tensors, {self.INPUT_TENSOR_NAME: inputs})
                elapsed = time.time() - t
                print("Duration: ", elapsed)

                result_array = outputs.pop(0)
                probability_array = outputs.pop(0)

                if probability_array[0] > 0.6:

                    result = result_array[0]
                    ol = (int(result[0] * width), int(result[1] * height))
                    ur = (int(result[2] * width), int(result[3] * height))
                    color = (0, 0, 255)

                    enemy_width = (result[0] - result[2])
                    enemy_height = (result[1] - result[3])

                    estimated_distance = (650*14.86)/(enemy_height * height)
                    estimated_rotation_to_enemy = (0.5-(result[0] + 0.5 * enemy_width)) * -90

                    cv.rectangle(frame, ol, ur, color)

                cv.imshow(window_name, frame)
                    
                key = cv.waitKey(10)
                if key == ord('q') or key == 27:
                    break


def take_picture_to_byte(image):

    with io.BytesIO() as output:
        image.save(output, 'BMP')
        image_as_bytes = output.getvalue()

    return image_as_bytes

def detect_object(mode):

    if mode == "online":
        videoprocessor = VideoProcessingCloud()

    
        videoprocessor.detection()
        print('Duration:', elapsed)

    elif mode == "offline":
        od_model = VideoProcessingTF(MODEL_FILENAME)
        od_model.predict_image()


if __name__ == "__main__":
    detect_object("offline")

