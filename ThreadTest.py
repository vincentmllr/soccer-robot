import anki_vector
import anki_vector.util
import threading
import time
from anki_vector.util import degrees, distance_mm, speed_mmps


def main():  
        
    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial) as robot:  
        def shooting():
            while  running:
                robot.behavior.set_lift_height(0.7,accel=100.0, max_speed=100.0, duration=0.0)
                #time.sleep(0.05)
                robot.behavior.set_lift_height(0.0, accel=100.0, max_speed=100.0, duration=0.0)
                #time.sleep(0.05)
        def driving():  
            robot.behavior.drive_straight(distance_mm(550), speed_mmps(500)

        thread2 = threading.Thread(target=shooting)
        thread1 = threading.Thread(target=driving)
        thread1.start()
        thread2.start()
        thread1.join() 
    

    

if __name__ == "__main__":
    main()
                 