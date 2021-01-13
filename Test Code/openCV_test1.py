from __future__ import print_function
import cv2 as cv
import argparse
import imutils
import math

FOCALLENGTH = 4.25
show_window_camera = 1
show_window_ball = 1
show_window_goal_self = 1
show_window_goal_enemy = 1

al_camera = False
al_ball = False
al_goal_self = False


class Mask_window():

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
        self.is_master = is_master
        

    def get_values(self):
        return (self.low_H, self.low_S, self.low_V), (self.high_H, self.high_S, self.high_V)
    
    def preprocess(self, frame_HSV):
        frame_threshold = cv.inRange(frame_HSV, (self.low_H, self.low_S, self.low_V), (self.high_H, self.high_S, self.high_V))
        frame_threshold = cv.erode(frame_threshold, None, iterations=2)
        frame_threshold = cv.dilate(frame_threshold, None, iterations=2)
        return frame_threshold

    def calculate_rotation(self, goal_rotation, dist, x, y, left_angle, right_angle, width):
        rotation_to_z = None
        if right_angle > 90:
            rotation_to_z = goal_rotation - 90 - left_angle + (width/2 - x)
        if right_angle < 90:
            rotation_to_z = goal_rotation - 90 + right_angle + (width/2 - x)

        rotation_to_z = rotation_to_z % 360
        return rotation_to_z
    
    def round_to_interval(self, val):
        val = max(val, -1)
        val = min(val, 1)
        return val

    def find_ball(self, frame_threshold, frame):
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
                dist = (400*FOCALLENGTH)/radius
                estimated_rotation_to_ball = (-0.5 + (x/1277.5)) * 2 * 45

    def find_goal(self, frame_threshold, frame, width, goal_rotation):
        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        cnts = cv.findContours(frame_threshold.copy(), cv.RETR_EXTERNAL,
            cv.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        center1 = None
        center2 = None

        # only proceed if at least one contour was found
        if len(cnts) > 1:
            # find the largest contour in the mask, then use
            # it to compute the minimum enclosing circle and
            # centroid 
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


            # only proceed if the radius meets a minimum size
            if radius1 > 10 and radius2 > 10:
                # draw the circle and centroid on the frame,
                # then update the list of tracked points
                cv.circle(frame, (int(x1), int(y1)), int(radius1),
                    (255, 0, 0), 2)
                cv.circle(frame, center1, 5, (0, 0, 255), -1)
                
                cv.circle(frame, (int(x2), int(y2)), int(radius2),
                    (255, 0, 0), 2)
                cv.circle(frame, center2, 5, (0, 0, 255), -1)

                # Distanzberechnung mit ausgleich für die Höhe
                
                dist_a = (400*FOCALLENGTH)/radius1
                dist_b = (400*FOCALLENGTH)/radius2
                # dist_a = math.sqrt(math.pow(dist_a, 2) - 49)
                # dist_b = math.sqrt(math.pow(dist_b, 2) - 49)
                dist_c = 20

                # Winkel aus Dreieck mit Markerpunkten und Kamera
                pre_alpha = (pow(dist_a, 2) - pow(dist_b, 2) - pow(dist_c, 2)) / (-2 * dist_b * dist_c)
                alpha = math.acos(self.round_to_interval(pre_alpha))
                pre_beta = (pow(dist_b, 2) - pow(dist_a, 2) - pow(dist_c, 2)) / (-2 * dist_a * dist_c)
                beta = math.acos(self.round_to_interval(pre_beta))
                delta = 180 - beta
                epsilon = 180 - alpha

                if goal_rotation == 180:
                    if dist_a < dist_b:
                        x_self = (math.sin(delta) * dist_a)
                        vector_rotation = self.calculate_rotation(goal_rotation, dist_a, x1, y1, delta, beta, width)   
                        if beta > 90:
                            y_self = 400 - (math.cos(delta) * dist_a)
                        elif beta < 90:
                            y_self = 400 + (math.cos(beta) * dist_a)
                    elif dist_b < dist_a:
                        x_self = (math.sin(epsilon) * dist_b)
                        vector_rotation = self.calculate_rotation(goal_rotation, dist_b, x2, y2, alpha, epsilon, width) 
                        if alpha > 90:
                            y_self = 600 + (math.cos(delta) * dist_b)
                        elif alpha < 90:
                            y_self = 600 - (math.cos(beta) * dist_b)

                elif goal_rotation == 0:
                    if dist_a < dist_b:
                        x_self = 1600 - (math.sin(delta) * dist_a)
                        vector_rotation = self.calculate_rotation(goal_rotation, dist_a, x1, y1, delta, beta, width) 
                        if beta > 90:
                            y_self = 600 + (math.cos(delta) * dist_a)
                        elif beta < 90:
                            y_self = 600 - (math.cos(beta) * dist_a)
                    elif dist_b < dist_a:
                        x_self = 1600 - (math.sin(epsilon) * dist_b)
                        vector_rotation = self.calculate_rotation(goal_rotation, dist_b, x2, y2, alpha, epsilon, width) 
                        if alpha > 90:
                            y_self = 400 - (math.cos(delta) * dist_b)
                        elif alpha < 90:
                            y_self = 400 + (math.cos(beta) * dist_b)   

                print(dist_a, dist_b, vector_rotation)
                 # env.position_x(x_self)
                 # env.position_y(y_self)
                 # env.rotation(vector_rotation)


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

            cv.createTrackbar(self.low_H_name, self.window_name, self.low_H, self.max_value_H, on_low_H_thresh_trackbar)
            cv.createTrackbar(self.high_H_name, self.window_name, self.high_H, self.max_value_H, on_high_H_thresh_trackbar)
            cv.createTrackbar(self.low_S_name, self.window_name, self.low_S, self.max_value, on_low_S_thresh_trackbar)
            cv.createTrackbar(self.high_S_name, self.window_name, self.high_S, self.max_value, on_high_S_thresh_trackbar)
            cv.createTrackbar(self.low_V_name, self.window_name, self.low_V, self.max_value, on_low_V_thresh_trackbar)
            cv.createTrackbar(self.high_V_name, self.window_name, self.high_V, self.max_value, on_high_V_thresh_trackbar)

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




class TrackBall():

    def __init__(self):
        self.window_capture_name = 'Vectors Camera'
        self.window_detection_name_ball = 'Ball Detection'
        self.window_detection_name_goal_self = 'Goal Detection'
        self.window_master_name = "Master"
   
    def start(self):

        parser = argparse.ArgumentParser(description='Code for Thresholding Operations using inRange tutorial.')
        parser.add_argument('--camera', help='Camera divide number.', default=0, type=int)
        args = parser.parse_args()
        cap = cv.VideoCapture(args.camera)

        cv.namedWindow(self.window_capture_name, cv.WINDOW_NORMAL)
        cv.namedWindow(self.window_detection_name_ball, cv.WINDOW_NORMAL)
        cv.namedWindow(self.window_detection_name_goal_self, cv.WINDOW_NORMAL)
        cv.namedWindow(self.window_master_name, cv.WINDOW_NORMAL)

        exist_camera = True
        exist_ball = True
        exist_goal = True

        cv.moveWindow(self.window_capture_name, 0, -100)
        cv.moveWindow(self.window_detection_name_ball, 550, -1)
        cv.moveWindow(self.window_detection_name_goal_self, 0, 230)
        cv.moveWindow(self.window_master_name, 700, 0)

        master_trackbar = Mask_window(self.window_master_name, 0, 0, 0, 0, 0, 0, True)
        master_trackbar.build_window()

        mask_ball = Mask_window(self.window_detection_name_ball, 6, 104, 140, 60, 242, 195, False)
        mask_ball.build_window()

        mask_goal = Mask_window(self.window_detection_name_goal_self, 6, 104, 140, 60, 242, 195, False)
        mask_goal.build_window()

        

        while True:
            
            ret, frame = cap.read()
            if frame is None:
                break
            #width, height = frame.size
            width = 635
            frame_HSV = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            frame_threshold_ball = mask_ball.preprocess(frame_HSV)
            frame_threshold_goal_self = mask_goal.preprocess(frame_HSV)

            mask_ball.find_ball(frame_threshold_ball, frame)
            mask_goal.find_goal(frame_threshold_goal_self, frame, width, 180)

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



            
            key = cv.waitKey(30)
            if key == ord('q') or key == 27:
                break

    


def run():
    tb = TrackBall()
    tb.start()

if __name__ == "__main__":
    run()