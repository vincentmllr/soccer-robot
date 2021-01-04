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




def test():

    robot = anki_vector.Robot(serial=SERIAL)
    robot.connect()
    robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange

    with behavior.ReserveBehaviorControl(serial=SERIAL):

        robot.behavior.set_head_angle(degrees(0))
        sf.drive_to_ball(robot)

    robot.disconnect()

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
        wait_until_enter = input()
        robot.behavior.set_head_angle(degrees(0))
        robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange
        print("Goooooo")
        print("postion anfang: ", env.self.position_x)
        print("postion anfang: ", env.self.position_y)
        
        print("detect_object()")
        detect_ball_Thread.start()
        # perception.detect_ball(robot, env)
        action.look_for_ball(env, robot)
        print("position Ende: ", env.self.position_x)
        print("position Ende: ", env.self.position_y)


# def main():

#     robot = anki_vector.Robot(serial=SERIAL)
#     environment = env.Environment(robot,
#                                   field_length_x=2000.0,
#                                   field_length_y=1000.0,
#                                   goal_width=200.0,
#                                   ball_diameter=40.0,
#                                   position_start_x=100.0,
#                                   position_start_y=500.0)

#     robot.connect()

#     with behavior.ReserveBehaviorControl(serial=SERIAL):

#         while True:

#             robot.behavior.drive_off_charger()

#             # perception.detect_objects(robot, environment)
#             # action.play_ball(robot, environment)

#     robot.disconnect()


if __name__ == "__main__":
    
    main()
    #test()
