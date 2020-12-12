import anki_vector
import perception
from anki_vector.util import *
import io

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

def take_picture_to_byte(robot):
    image = robot.camera.capture_single_image().raw_image

    with io.BytesIO() as output:
        image.save(output, 'BMP')
        image_as_bytes = output.getvalue()

    return image_as_bytes


def drive_to_ball(robot):
    pic = take_picture_to_byte(robot)
    poi = perception.detect_object(robot, "online", pic)
    if poi > 0.5:
        robot.behavior.turn_in_place(degrees(60-(poi*2)*60))
    elif poi < 0.5:
        robot.behavior.turn_in_place(degrees((poi-0.5) * -60))
    robot.behavior.drive_straight(distance_mm(100), speed_mmps(100))


    


def main():
    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial) as robot:
        distance(robot)

    


if __name__ == "__main__":
    main()