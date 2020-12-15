
import environment
import perception
import support_functions
import anki_vector
import anki_vector.util
import threading
import time
from anki_vector.util import degrees, distance_mm, speed_mmps



# args = anki_vector.util.parse_command_args()
# with anki_vector.Robot(args.serial) as robot:  

    def play_ball(env, robot):
        


    def shooting(env, robot):
       
       #Events zur Kommunikation zwischen den Threads
        ball_is_in_line = threading.Event()
        shoot_ball = threading.Event()

        def ball_still_in_line(robot):
            ''' Methode die als Thread ausgeführt wird.
            Prüft ob Vector noch auf den Ball zufährt und korrigiert gegebenfalls die Richtung'''

            ball_is_in_line.set()
            while not shoot_ball.is_set():
                pic = support_functions.take_picture_to_byte(robot)
                poi = perception.detect_object(robot, "online", pic)
                if poi > 0.55:
                    ball_is_in_line.clear()
                    robot.behavior.turn_in_place(degrees(45-(poi*2)*45))
                    ball_is_in_line.set()
                elif poi < 0.45:
                    ball_is_in_line.clear()
                    robot.behavior.turn_in_place(degrees((poi-0.5) * -45))
                    ball_is_in_line.set()

        def drive_and_shoot(env, robot):
            '''Methode die als Thread ausgeführt wird.
            Fährt gerade aus und activiert das shoot_ball-Event sobald sie nah genug am Ball ist.'''
            shoot_ball.clear()  
            while ball_is_in_line.is_set():
                #Berechnung für den Abstand zwischen Vector und Ball
                envObjList = env.environment_update(env)
                difference_x = envObjList[0].position_x - envObjList[1].position_x
                difference_y = envObjList[0].position_y - envObjList[1].position_y
                distance_to_ball = ((difference_x**2 + difference_y**2)**0.5)

                if distance_to_ball > 25:
                    robot.behavior.drive_straight(distance_mm(5), speed_mmps(500))
                elif distance_to_ball <=25:
                    shoot_ball.set()
                    robot.behavior.drive_straight(distance_mm(30), speed_mmps(500))
                    shoot_ball.clear()
                    ball_is_in_line.clear()

         def shoot(robot):
             '''Methode die als Thread ausgeführt wird.
             bewegt lift des Vectors auf und ab'''
                while shoot_ball.is_set():
                    robot.behavior.set_lift_height(0.7,accel=1000.0, max_speed=1000.0, duration=0.0)
                    robot.behavior.set_lift_height(0.0, accel=1000.0, max_speed=1000.0, duration=0.0)

        #erstellen der Threads
        ball_still_in_lineThread = threading.Thread(target=ball_still_in_line,args=[robot])
        drive_and_shootThread = threading.Thread(target=drive_and_shoot, args=[env,robot])
        shootThread = threading.Thread(target=shoot, args=[robot])
        
        #start der Threads
        drive_and_shootThread.start()
        ball_still_in_lineThread.start()
        shootThread.start()




            
            





       
        
       
            
    

    
        
        


    