import anki_vector
from anki_vector import behavior, connection
from anki_vector.util import *
import threading
import support_functions as sf
import perception
import action
import environment 

NAME = "Vector-N8G2"
IP = "192.168.0.189"
SERIAL = "008014c1"


def main():
    
    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial) as robot:
        env = environment.Environment(robot,
                                      field_length_x=2000.0,
                                      field_length_y=1000.0,
                                      goal_width=200.0,
                                      ball_diameter=40.0,
                                      position_start_x=100.0,
                                      position_start_y=500.0,
                                      enable_environment_viewer=False)
        print("Zum Starten Enter drücken")
        detect_ball_Thread = threading.Thread(target=perception.detect_ball, args=[robot, env])
        robot.behavior.set_head_angle(degrees(0))
        robot.camera.init_camera_feed()
        detect_ball_Thread.start()
        print("detect_ball()")
        wait_until_enter = input()
        robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange
        print("Goooooo")
        print("postion anfang: ", env.self.position_x)
        print("postion anfang: ", env.self.position_y)
        robot.behavior.drive_straight(distance_mm(50), speed_mmps(500))
        #action.look_for_ball(env, robot)
        print("position Ende: ", env.self.position_x)
        print("position Ende: ", env.self.position_y)




if __name__ == "__main__":
    
    main()
    #test()
