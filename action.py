
import environment
import math
import perception
import support_functions
import anki_vector
import anki_vector.util
import threading
import time
from anki_vector.util import degrees, distance_mm, speed_mmps, Angle, Pose


# args = anki_vector.util.parse_command_args()
# with anki_vector.Robot(args.serial) as robot:
x_goal_enemy = 2000
y_goal_enemy = 500

def play_ball(env, robot):
    '''Entscheidet, ob Vector offensiv oder defensiv spielen soll.
    (Ball zwischen gegnerischem Tor und Vector => offensiv)
    (Vector zwischen gegnerischem Tor und Ball => defensiv)
    '''

    if env.self.position_x < env.ball.position_x:
        play_offensive(env, robot)
    else:
        play_defensive(env, robot)


def play_offensive(env, robot):
    '''berechenet die notwendige Schussbahn, um ein Tor zu schießen.
    Lässt dann Vector zu dem Punkt 10cm hinter den Ball fahren, der in
    Verlängerung zur Schussbahn liegt.
    Anschließend wird der Vector in Richtung Tor gedreht und die Methode
    shooting(env, robot) aufgerufen
    '''
    x_ball = env.ball.position_x
    y_ball = env.ball.position_y
    print("Positon Ball: x = " + x_ball + "; y = " + y_ball)
    
    # Berechnung des Richtungsvektors
    x_direction = 1
    y_direction = (y_goal_enemy - y_ball)/(x_goal_enemy - x_ball)

    # Normieren des Richtungsvektors
    abs_value = ((x_direction**2)+(y_direction**2))**0.5  # Betrag
    x_direction_norm = (1/abs_value)*x_direction
    y_direction_norm = (1/abs_value)*y_direction

    # Berechnen der Koordinaten des Punktes [2] 10cm hinter dem Ball, in
    # Verlängerung zur Schussbahn, zu dem Vector fahren soll.
    x_vector_pos2 = -100 * x_direction_norm + x_ball
    y_vector_pos2 = -100 * y_direction_norm + x_ball
    print("Neu brechnete Position Vector: x = " + x_vector_pos2 + " y = " + y_vector_pos2)

    # Vector fährt von Positon 1 (aktuell) zur Position 2
    '''eventuell mit go_to_pose(pose)'''
    
    # y_vector_pos1 = env.self.position_y
    # x_vector_pos1 = env.self.position_x
    # countered_leg = y_vector_pos2 - y_vector_pos1  # Gegenkathete
    # adjacent_leg = x_vector_pos2 - x_vector_pos1  # Ankathete
    # angle_rad_pos2 = math.atan2(countered_leg, adjacent_leg)  # Winkel zwischen x-Achse und Gerade zwischen Postion 1 und 2 (Bogenmaß)
    # angle_deg_pos2 = math.degrees(angle_rad_pos2)  # Winkel in Grad

    # # Berechenen des winkels um den sich Vector drehen muss
    # if angle_deg_pos2 < 0:
    #     angle_deg_pos2 = 360 + angle_deg_pos2  # eventuell Umwandlung in positiven Winkel
    
    # angle_deg_vector = env.self.rotation  # aktuelle Rotation des Vectors
    # turning_angle = 360 - angle_deg_vector + angle_deg_pos2  # Berechenen des Winkels um den sich Vector drehen muss

    # if turning_angle > 360:
    #     turning_angle = turning_angle - 360  # Winkel nicht größer als 360 Grad

    # if turning_angle > 180:
    #     turning_angle = turning_angle - 360  # Drehung nicht mehr als 180 Grad

    turning_angel = turning_angel_vector(env, x_vector_pos2, y_vector_pos2) # Berechenen des Winkels um den sich Vector drehen muss (Positon 1)
    robot.behavior.turn_in_place(degrees(turning_angel))  # Vector dreht sich auf Position 1

    y_vector_pos1 = env.self.position_y
    x_vector_pos1 = env.self.position_x
    distance_p1_p2 = ((y_vector_pos2 - y_vector_pos1)**2 + (x_vector_pos2 - x_vector_pos1)**2)**0.5  # Strecke zwischen Position 1 und 2
    robot.behavior.drive_straight(distance_mm(distance_p1_p2), speed_mmps(500)) # Vector fährt zu Position 2

    turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) # Berechenen des Winkels um den sich Vector drehen muss (Position 2)
    robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich auf Position 1

    shooting(env, robot)  # Vector fährt zum Ball und schießt




def turning_angel_vector(env, endposition_x, endposition_y):
    '''Berechnet Winkel, um den sich Vector auf der Stelle drehen muss,
    um danach auf einer Gerade vom aktuellen Standort zur Endposition zu fahren.
    '''
    startpositon_y = env.self.position_y
    startpositon_x = env.self.position_x
    countered_leg = endposition_y - startpositon_y  # Gegenkathete
    adjacent_leg = endposition_x - startpositon_x  # Ankathete
    angle_rad_pos2 = math.atan2(countered_leg, adjacent_leg)  # Winkel zwischen x-Achse und Gerade zwischen Postion 1 und 2 (Bogenmaß)
    angle_deg_pos2 = math.degrees(angle_rad_pos2)  # Winkel in Grad

    # Berechenen des winkels um den sich Vector drehen muss
    if angle_deg_pos2 < 0:
        angle_deg_pos2 = 360 + angle_deg_pos2  # eventuell Umwandlung in positiven Winkel
    
    angle_deg_vector = env.self.rotation  # aktuelle Rotation des Vectors
    turning_angle = 360 - angle_deg_vector + angle_deg_pos2  # Berechenen des Winkels um den sich Vector drehen muss

    if turning_angle > 360:
        turning_angle = turning_angle - 360  # Winkel nicht größer als 360 Grad
    
    if turning_angle > 180:
        turning_angle = turning_angle - 360  # Drehung nicht mehr als 180 Grad

    return turning_angle


def shooting(env, robot):
    ''' Vector fährt auf Ball zu, korregiert eventuell Fahrtrichtung.
    Ist er nah genug am Ball, soll er mit Hilfe seines Lifts schießen
    '''

    # Events zur Kommunikation zwischen den Threads
    ball_is_in_line = threading.Event()
    shoot_ball = threading.Event()

    def ball_still_in_line(robot):
        ''' Methode die als Thread ausgeführt wird.
        Prüft ob Vector noch auf den Ball zufährt und korrigiert
        gegebenfalls die Richtung
        '''

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
        Fährt gerade aus und activiert das shoot_ball-Event
        sobald sie nah genug am Ball ist.
        '''
        shoot_ball.clear()
        while ball_is_in_line.is_set():
            
            # Berechnung für den Abstand zwischen Vector und Ball
            difference_x = env.self.position_x - env.ball.position_x
            difference_y = env.self.position_y - env.ball.position_y
            distance_to_ball = ((difference_x**2 + difference_y**2)**0.5)

            if distance_to_ball > 25:
                robot.behavior.drive_straight(distance_mm(5), speed_mmps(500))
            elif distance_to_ball <= 25:
                shoot_ball.set()
                robot.behavior.drive_straight(distance_mm(30), speed_mmps(500))
                shoot_ball.clear()
                ball_is_in_line.clear()

    def shoot(robot):
        '''Methode die als Thread ausgeführt wird.
        bewegt lift des Vectors auf und ab'''
        while shoot_ball.is_set():
            robot.behavior.set_lift_height(0.7, accel=1000.0, max_speed=1000.0, duration=0.0)
            robot.behavior.set_lift_height(0.0, accel=1000.0, max_speed=1000.0, duration=0.0)

    # erstellen der Threads
    ball_still_in_lineThread = threading.Thread(target=ball_still_in_line, args=[robot])
    drive_and_shootThread = threading.Thread(target=drive_and_shoot, args=[env, robot])
    shootThread = threading.Thread(target=shoot, args=[robot])

    # start der Threads
    drive_and_shootThread.start()
    ball_still_in_lineThread.start()
    shootThread.start()
