import anki_vector
from anki_vector import behavior, connection
from anki_vector.util import *
from anki_vector.connection import ControlPriorityLevel
import time
import threading
import tkinter

import perception
import action
import environment

NAME = "Vector-N8G2"
NAME_VINCENT = 'Vector-R7U1'
IP = "192.168.0.189"
IP_VINCENT = '192.168.68.159'
SERIAL = "008014c1"
SERIAL_VINCENT = '00804ea0'
IP_TIM = "192.168.178.47"
NAME_TIM = "Vector-C9F7"
SERIAL_TIM = "009009e9"



def main():
    
    robot = anki_vector.Robot(serial=SERIAL)
    robot.connect()
    #  robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange
    robot.behavior.set_eye_color(0.57, 1.0)  # Augenfarbe sapphire

    env = environment.Environment(robot,
                                  field_length_x=1500.0,
                                  field_length_y=1000.0,
                                  goal_width=200.0,
                                  ball_diameter=40.0,
                                  position_start_x=750.0,
                                  position_start_y=500.0)

    detect_ball_Thread = threading.Thread(target=perception.detect_openCV, args=[robot, env])
    detect_enemy_Thread = threading.Thread(target=perception.detect_enemy, args=[robot, env, "online"])
    robot.behavior.set_head_angle(degrees(0))
    robot.behavior.set_lift_height(0)
    print("detect_ball()")
    robot.camera.init_camera_feed()
    detect_ball_Thread.start()  # Start der Ballerkennung als Thread
    #detect_enemy_Thread.start()
    print("Zum Starten des Enviroment Viewers Enter drücken")
    input()
    robot.behavior.set_head_angle(degrees(0))
    env.environment_viewer.start()
    print("x-postion anfang: ", env.self.position_x, "y-postion anfang: ", env.self.position_y, "Rotation Vector: ", env.self.rotation)
    print()
    # robot.behavior.turn_in_place(degrees(90))
    # robot.behavior.drive_straight(distance_mm(300),speed_mmps(500))
    # robot.behavior.turn_in_place(degrees(-90))
    print("Zum Starten des Spiels Enter drücken")
    input()
    robot.behavior.set_head_angle(degrees(0))
    robot.behavior.set_lift_height(0)
    print("ANPFIFF")

    while True:
        action.look_for_ball(env, robot)
        
    robot.disconnect()


def test():

    robot = anki_vector.Robot(serial=SERIAL)
    robot.connect()
    robot.behavior.set_eye_color(0.57, 1.0)  # Augenfarbe sapphire

    env = environment.Environment(robot,
                                  field_length_x=1500.0,
                                  field_length_y=1000.0,
                                  goal_width=200.0,
                                  ball_diameter=40.0,
                                  position_start_x=300.0,
                                  position_start_y=500.0)

    detect_ball_Thread = threading.Thread(target=perception.detect_openCV, args=[robot, env])
    #detect_enemy_Thread = threading.Thread(target=perception.detect_enemy, args=[robot, env, "online"])
    robot.behavior.set_head_angle(degrees(0))
    robot.behavior.set_lift_height(0)
    print("detect_ball()")
    robot.camera.init_camera_feed()
    detect_ball_Thread.start() # Start des der Ballerkennung als Thread
    # print("Zum Starten des Enviroment Viewers Enter drücken")
    # input()
    # robot.behavior.set_head_angle(degrees(0))
    # env.environment_viewer.start()
    # print("x-postion anfang: ", env.self.position_x)
    # print("y-postion anfang: ", env.self.position_y)
    # print("Rotation Vector: ", env.self.rotation)
    # print()
    print("Zum Starten des Spiels Enter drücken")
    input()
    robot.behavior.set_head_angle(degrees(0))
    robot.behavior.set_lift_height(0)
    print("ANPFIFF")
    running = True
    while True:
        print(env.ball.is_seen())
        time.sleep(0.5)
    robot.disconnect()
     

if __name__ == "__main__":
    #main()
    test() 