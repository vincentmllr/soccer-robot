import os
import time

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateEntry, Region
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials

from PIL import Image

# import support_functions
# import environment

class cloud_predict():


    def __init__(self):

        self.ENDPOINT = "https://vector.cognitiveservices.azure.com/"
        self.prediction_key = "a9f0177e6df54a63a7d6cc9477c383f9"
        self.prediction_resource_id = "/subscriptions/f6e54442-3d5a-4083-ad0d-080f159ac33d/resourceGroups/Vision/providers/Microsoft.CognitiveServices/accounts/Vector"
        self.project_id = "d2693bf6-e18a-414f-bdba-2851847b43a0"
        self.publish_iteration_name = "Iteration3"
        
        self.prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": self.prediction_key})
        self.predictor = CustomVisionPredictionClient(self.ENDPOINT, self.prediction_credentials)

        
    def prediction(self, image):
        time = time.time()
        with open(image, mode="rb") as prediction_image:
            prediction_results = self.predictor.detect_image(self.project_id, self.publish_iteration_name, prediction_image)

        # Display the results.
        for prediction in prediction_results.predictions:
            print("\t" + prediction.tag_name + ": {0:.2f}% bbox.left = {1:.2f}, bbox.top = {2:.2f}, bbox.width = {3:.2f}, bbox.height = {4:.2f}".format(
                prediction.probability * 100, prediction.bounding_box.left, prediction.bounding_box.top, prediction.bounding_box.width, prediction.bounding_box.height))

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
            #         FO = field_object(ball, estimated_x, estimated_y, time)

            # if prediciton.tag_name == 'Ball':
            #     if prediction.probability > 0.4:
            #         estimated_distance = 3 - prediction.bounding_box.height * 10
            #         if estimated_distance < 100:
            #             object_distance = distance(robot)
            #             if object_distance is not None:
            #                 estimated_distance = object_distance
            #         estimated_x = robot.position.x + (math.cos(robot.rotation.q0) * estimated_distance)
            #         estimated_y = robot.position.y + (math.sin(robot.rotation.q0) * estimated_distance)
            #         FO = field_object(ball, estimated_x, estimated_y, time)


  

#Class to define an object on the map with the name, coordinates and timestamp of the predicted picture
class field_object():
    
    def __init__(Tag, X_Coordinate, Y_Coordinate, time):
        self.tag = Tag
        self.x_Coordinate = X_Coordinate
        self.y_Coordinate = Y_Coordinate
        self.moment = time


    

def main(image):
    predictor = cloud_predict()
    t = time.time()
    predictor.prediction('Ball14cm.png')
    #predictor.prediction(image)
    elapsed = time.time() - t
    print('Duration:', elapsed)


if __name__ == "__main__":
    main(None)