import anki_vector
from anki_vector import behavior, connection
from anki_vector.util import *
import threading
import support_functions as sf
import perception
import action
import environment
import time
import tkinter

NAME = "Vector-N8G2"
NAME_VINCENT = 'Vector-R7U1'
IP = "192.168.0.189"
IP_VINCENT = '192.168.68.159'
SERIAL = "008014c1"
SERIAL_VINCENT = '00804ea0'


def main():

    robot = anki_vector.Robot(serial=SERIAL_VINCENT)
    robot.connect()
    robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange

    env = environment.Environment(robot,
                                  field_length_x=2000.0,
                                  field_length_y=1000.0,
                                  goal_width=200.0,
                                  ball_diameter=40.0,
                                  position_start_x=500.0,
                                  position_start_y=500.0)

    with behavior.ReserveBehaviorControl(serial=SERIAL_VINCENT):

        # #+++EnvironmentViewerTestANFANG+++
        def show_viewer():
            viewer = environment.EnvironmentViewer(env)
            fenster = tkinter.Tk()
            app = viewer.TestWindow(fenster)
            fenster.mainloop()

        viewer_thread = threading.Thread(target=show_viewer())
        viewer_thread.start()
        # #+++EnvironmentViewerTestENDE+++

        detect_ball_Thread = threading.Thread(target=perception.detect_ball, args=[robot, env])
        robot.behavior.set_head_angle(degrees(0))
        robot.behavior.set_lift_height(0)
        print("detect_ball()")
        robot.camera.init_camera_feed()
        detect_ball_Thread.start()
        
        print("Zum Starten Enter drücken")
        input()

        robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange
        print("Goooooo")
        print("x-postion anfang: ", env.self.position_x)
        print("y-postion anfang: ", env.self.position_y)
        print("Rotation Vector: ", env.self.rotation)
        action.look_for_ball(env, robot)
        print("x-position Ende: ", env.self.position_x)
        print("y-position Ende: ", env.self.position_y)
        time.sleep(3)

        robot.disconnect()


def test():

    robot = anki_vector.Robot(serial=SERIAL_VINCENT)
    robot.connect()
    robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange

    env = environment.Environment(robot,
                                  field_length_x=2000.0,
                                  field_length_y=1000.0,
                                  goal_width=200.0,
                                  ball_diameter=40.0,
                                  position_start_x=500.0,
                                  position_start_y=500.0)

    detect_ball_Thread = threading.Thread(target=perception.detect_openCV, args=[robot, env])
    robot.behavior.set_head_angle(degrees(0))
    robot.behavior.set_lift_height(0)
    print("detect_ball()")
    robot.camera.init_camera_feed()
    detect_ball_Thread.start()
    env.environment_viewer.start()

    print("Zum Starten Enter drücken")
    input()
    robot.behavior.set_head_angle(degrees(0))
    robot.behavior.set_lift_height(0)
    running = True
    while running:
        print("Goooooo")
        print("x-postion anfang: ", env.self.position_x)
        print("y-postion anfang: ", env.self.position_y)
        print("Rotation Vector: ", env.self.rotation)
        action.look_for_ball(env, robot)
        print("x-position Ende: ", env.self.position_x)
        print("y-position Ende: ", env.self.position_y)
        print("zum abbrechen 0 drücken")
        i = input()
        if i == "0":
            running = False
     

if __name__ == "__main__":
    # main()
    test()