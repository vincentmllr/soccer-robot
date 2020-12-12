import anki_vector
from anki_vector.util import *

import support_functions as sf
import perception
#import action
#import environment


IP_ADDRESS = '192.#########'
SERIAL = '008014c1'
robot = anki_vector.robot

def test():

    args = anki_vector.util.parse_command_args()

    with anki_vector.Robot(args.serial) as robot:
        
        robot.behavior.set_head_angle(degrees(0))
        sf.drive_to_ball(robot)





def main():

    map=map.Map()
    robot=anki_vector.Robot()

    #Folgendes lieber als Methoden falls es geht oder stattdessen eine Methode initialize()
    args = anki_vector.util.parse_command_args()
    with behavior.ReserveBehaviorControl(serial = SERIAL, ip=IP_ADDRESS):
        


        with anki_vector.Robot(serial = SERIAL,
                                name='Vector-N8G2',
                                ip=IP_ADDRESS,
                                behavior_control_level=ControlPriorityLevel.OVERRIDE_BEHAVIORS_PRIORITY
                                ) as robot:
            
            while True:
                
                perception.detect_objects(robot, map)
                action.play_ball(map)

if __name__ == "__main__":
    #main()
    test()
