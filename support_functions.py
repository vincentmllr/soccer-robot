import anki_vector

#Returns Distance of Object in front of Vector
def distance(robot):

    print("Reading proximity sensor. ")
    signal = robot.proximity.last_sensor_reading
    proximity_distance = None
    if signal is not None:
        print('Proximity distance: {0}'.format(signal.distance))
        if signal.signal_quality > 0.5:
            proximity_distance = signal.distance.distance_mm

    return proximity_distance

                    
def CustomDetection(robot):
    robot.enable_custom_object_detection(true)

def take_picture(robot):
    image = robot.camera.capture_single_image().raw_image
    return image

    


def main():
    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial) as robot:
        distance(robot)

    


if __name__ == "__main__":
    main()