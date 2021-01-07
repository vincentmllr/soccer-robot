import anki_vector
from anki_vector import behavior, connection
from anki_vector.util import *
import threading
import support_functions as sf
import perception
import action
import environment
import time
from tkinter import *

NAME = "Vector-N8G2"
IP = "192.168.0.189"
SERIAL = "008014c1"


def main():

    robot = anki_vector.Robot(serial=SERIAL)
    robot.connect()
    robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange

    env = environment.Environment(robot,
                                  field_length_x=2000.0,
                                  field_length_y=1000.0,
                                  goal_width=200.0,
                                  ball_diameter=40.0,
                                  position_start_x=500.0,
                                  position_start_y=500.0,
                                  enable_environment_viewer=False)

    with behavior.ReserveBehaviorControl(serial=SERIAL):

        # #+++EnvironmentViewerTestANFANG+++
        viewer = environment.EnvironmentViewer(env)
        # viewer_thread = threading.Thread(target=viewer.show())
        # viewer_thread.start()
        fenster = Tk()
        app = viewer.TestWindow(fenster)
        fenster.wm_title("Testfenster")
        #Show window
        fenster.mainloop()
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

    robot = anki_vector.Robot(serial=SERIAL)
    robot.connect()
    robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange

    env = environment.Environment(robot,
                                  field_length_x=2000.0,
                                  field_length_y=1000.0,
                                  goal_width=200.0,
                                  ball_diameter=40.0,
                                  position_start_x=500.0,
                                  position_start_y=500.0,
                                  enable_environment_viewer=False)

    with behavior.ReserveBehaviorControl(serial=SERIAL):

            detect_ball_Thread = threading.Thread(target=perception.detect_ball, args=[robot, env])
            robot.behavior.set_head_angle(degrees(0))
            robot.behavior.set_lift_height(0)
            print("detect_ball()")
            robot.camera.init_camera_feed()
            detect_ball_Thread.start()

            print("Zum Starten Enter drücken")
            input()
            robot.behavior.drive_straight(distance_mm(40), speed_mmps(500))
            print("40mm")
            robot.behavior.drive_straight(distance_mm(40), speed_mmps(500))
            print("40mm")
            robot.behavior.drive_straight(distance_mm(40), speed_mmps(500))
            print("40mm")
            robot.behavior.drive_straight(distance_mm(40), speed_mmps(500))
            print("40mm")
            # action.shooting(env, robot)


if __name__ == "__main__":
    # main()
    test()