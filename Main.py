import anki_vector
from anki_vector import behavior, connection
#import perception
#import action
import environment as env

NAME = "Vector-N8G2"
IP = "192.168.0.189"
SERIAL = "008014c1"

def test():

    robot = anki_vector.Robot(serial = SERIAL)
    robot.connect()

    while True:

        robot.behavior.drive_off_charger()

        robot.behavior.drive_on_charger()

        robot.disconnect()


def main():

    environment = env.Environment()
    robot = anki_vector.Robot(serial = SERIAL)
    robot.connect()

    with behavior.ReserveBehaviorControl(serial= SERIAL):

        while True:

            #perception.detect_objects(robot, environment)
            #action.play_ball(robot, environment)

    robot.disconnect()


if __name__ == "__main__":
    #main()
    test()