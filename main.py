import anki_vector
from anki_vector import behavior, connection
from anki_vector.util import *
import support_functions as sf
#import perception
#import action
import environment as env

NAME = "Vector-N8G2"
IP = "192.168.0.189"
SERIAL = "008014c1"

def test():

    robot = anki_vector.Robot(serial = SERIAL)
    robot.connect()
    robot.behavior.set_eye_color(0.05, 1.0) #Augenfarbe orange
        
    with behavior.ReserveBehaviorControl(serial= SERIAL):

        robot.behavior.set_head_angle(degrees(0))
        sf.drive_to_ball(robot)

    robot.disconnect()


def main():

    robot = anki_vector.Robot(serial = SERIAL)
    environment = env.Environment(robot, field_length_x=2000.0, field_length_y=1000.0, position_start_x=100.0, position_start_y=500.0)

    robot.connect()

    with behavior.ReserveBehaviorControl(serial= SERIAL):

        while True:

            robot.behavior.drive_off_charger()

            #perception.detect_objects(robot, environment)
            #action.play_ball(robot, environment)

    robot.disconnect()


if __name__ == "__main__":
    #main()
    test()
