import anki_vector
from anki_vector.util import *
import perception
#import gameplay
#import map
import support_functions as sf


IP_ADDRESS = '192.168.0.136'
SERIAL = '008014c1'
#robot = anki_vector.robot()


def main():

#    map=map.Map()
    robot=anki_vector.Robot()

    #Folgendes lieber als Methoden oder stattdessen eine Methode initialize()
    args = anki_vector.util.parse_command_args()

    with anki_vector.Robot(args.serial) as robot:
        robot.behavior.set_head_angle(degrees(0))
        sf.drive_to_ball(robot)
        
    


if __name__ == "__main__":
    main()