import anki_vector
import environment


IP_ADDRESS = '192.#########'
SERIAL = '008014c1'
robot = anki_vector.robot


def main():
    args = anki_vector.util.parse_command_args()
    with behavior.ReserveBehaviorControl(serial = SERIAL, ip=IP_ADDRESS):

        with anki_vector.Robot(serial = SERIAL, name='Vector-N8G2', ip=IP_ADDRESS, behavior_control_level=ControlPriorityLevel.OVERRIDE_BEHAVIORS_PRIORITY) as robot:
            
            online_predictor = cloud_predict()
            







            # An dieser Stelle Entscheidungslogik einfügen

    


if __name__ == "__main__":
    main()