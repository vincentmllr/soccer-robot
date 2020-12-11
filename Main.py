import anki_vector
import perception
import gameplay
import map


IP_ADDRESS = '192.#########'
SERIAL = '008014c1'
robot = anki_vector.robot


def main():

    map=map.Map()
    robot=anki_vector.Robot()

    #Folgendes lieber als Methoden oder stattdessen eine Methode initialize()
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
    main()