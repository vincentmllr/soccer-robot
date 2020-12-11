import anki_vector
import anki_vector.util
import threading
import time
from anki_vector.util import degrees, distance_mm, speed_mmps

def drivingAndShooting(distance = 550):
    running = True
    def driving():
            
        robot.behavior.drive_straight(distance_mm(distance), speed_mmps(500)
                
    def shooting():
        while  running:
             robot.behavior.set_lift_height(0.7,accel=100.0, max_speed=100.0, duration=0.0)
             #time.sleep(0.05)
             robot.behavior.set_lift_height(0.0, accel=100.0, max_speed=100.0, duration=0.0)
             #time.sleep(0.05)   

   


def main():
    
        thread1 = threading.Thread(target=driving)
        thread2 = threading.Thread(target=shooting)
        thread1.start()
        thread2.start()
        thread1.join()
        
        
    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial) as robot:  
        drivingAndShooting()  
    

    

if __name__ == "__main__":
    main()
                 
