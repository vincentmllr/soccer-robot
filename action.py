import environment
import math
import perception
import support_functions
import anki_vector
import anki_vector.util
import threading
import time
from anki_vector.util import degrees, distance_mm, speed_mmps, Angle, Pose

x_goal_enemy = 2000
y_goal_enemy = 500
x_goal_self = 0
y_goal_self = 500


def look_for_ball(env, robot):
    '''Vector dreht sich so lange bis er Ball gefunden hat,
    ruft dann play_ball auf.
    '''
    print("look_for_ball()")
    ball_is_seen = env.ball.is_seen()
    degrees_turned = 0
    while not ball_is_seen:
        if degrees_turned == 360:
            print("Ball not found")
            # robot.behavior.drive_straight(distance_mm(300), speed_mmps(500))
            play_defensive(env, robot)
            degrees_turned = 0
        robot.behavior.turn_in_place(degrees(45))
        degrees_turned = degrees_turned + 45
        ball_is_seen = env.ball.is_seen()
    print("ball found")
    print("Rotation Vector: ", env.self.rotation)
    print("sleep")
    time.sleep(0.2)  # Verzögerung Kamera-Feed ausgleichen
    print("wake up")
    print("Rotation to Ball: ", perception.current_rotation_to_ball())
    if perception.current_rotation_to_ball() is not None:
        robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball

    print("turn to ball")
    distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
    print("Distanz zum Ball: ", distance_to_ball)
    play_ball(env, robot)
    

def play_ball(env, robot):
    '''Entscheidet, ob Vector offensiv oder defensiv spielen soll.
    (Ball zwischen gegnerischem Tor und Vector => offensiv)
    (Vector zwischen gegnerischem Tor und Ball => defensiv)
    '''
    print("play_ball()")
    if ((env.self.rotation < 90) & (env.self.rotation > -90)):
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
    print("play_offensive()")
    unobstructed = robot.proximity.last_sensor_reading.unobstructed
    distance_to_ball = 0.0
    if not unobstructed:
        distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
        print("Distanz zu Ball: ", distance_to_ball)
    while unobstructed | (distance_to_ball > 100):  # Vector soll bis 10 cm vor dem ball gerade auf ihn zufahren
        print("neue schleife", distance_to_ball)
        if perception.current_rotation_to_ball() is not None:
            robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
        robot.behavior.drive_straight(distance_mm(40), speed_mmps(500))
        unobstructed = robot.proximity.last_sensor_reading.unobstructed
        if not unobstructed:
            distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
            print("Distanz zu Ball: ", distance_to_ball)

    print("Distanz zu Ball: ", distance_to_ball)
    print("Laufbahn berechenen")
    print("x-postion : ", env.self.position_x)
    print("y-postion : ", env.self.position_y)

    # Koordinaten vom Ball bestimmen
    time.sleep(0.2) # Verzögerung Kamera-Feed ausgleichen
    if perception.current_rotation_to_ball() is not None:
        robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
    distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
    print("Distanz zu Ball infrarot: ", distance_to_ball)
    
    # approximierte Distanz:
    difference_x = env.self.position_x - env.ball.position_x
    difference_y = env.self.position_y - env.ball.position_y
    distance_to_ball_approx = ((difference_x**2 + difference_y**2)**0.5)
    print("Distanz zu Ball approximiert: ", distance_to_ball_approx)

    diffrence_infra_approx = abs(distance_to_ball - distance_to_ball_approx) # Unterschied zwischen beiden berechneten Abständen
    if (diffrence_infra_approx < 10 ): # Wenn unterschied nicht größer als 1 cm, mittelwert aus infrarot und approximierten Abstand zu Ball
        distance_to_ball = ((distance_to_ball + distance_to_ball_approx)/2)
    print("Distanz zu Ball : ", distance_to_ball)

    x_vector = env.self.position_x
    y_vector = env.self.position_y
    rotation_vector = env.self.rotation
    x_ball = x_vector + math.cos(rotation_vector)*distance_to_ball
    y_ball = y_vector + math.sin(rotation_vector)*distance_to_ball
    print("Positon Ball: x = ", x_ball, "; y = ",  y_ball)

    # print("Rotation Vector: ", env.self.rotation)
    # x_ball = env.ball.position_x
    # y_ball = env.ball.position_y
    
    # Berechnung des Richtungsvektors
    x_direction = 1
    y_direction = (y_goal_enemy - y_ball)/(x_goal_enemy - x_ball)

    # Normieren des Richtungsvektors
    abs_value = ((x_direction**2)+(y_direction**2))**0.5  # Betrag des Vectors
    x_direction_norm = (1/abs_value)*x_direction
    y_direction_norm = (1/abs_value)*y_direction

    # Berechnen der Koordinaten des Punktes [2] 8 cm hinter dem Ball, in
    # Verlängerung zur Schussbahn, zu dem Vector fahren soll.
    x_vector_pos2 = -50 * x_direction_norm + x_ball
    y_vector_pos2 = -50 * y_direction_norm + y_ball
    print("Neu brechnete Position Vector: x = ", x_vector_pos2 , " y = ", y_vector_pos2)

    # Vector fährt von Positon 1 (aktuell) zur Position 2
    '''eventuell mit go_to_pose(pose)'''

    # turning_angel = turning_angel_vector(env, x_vector_pos2, y_vector_pos2) # Berechenen des Winkels um den sich Vector drehen muss (Positon 1)
    # print("Turning-Angle zur Position 2: ", turning_angel)
    # robot.behavior.turn_in_place(degrees(turning_angel))  # Vector dreht sich auf Position 1
    # print("turning")

    # y_vector_pos1 = env.self.position_y
    # x_vector_pos1 = env.self.position_x
    # distance_p1_p2 = ((y_vector_pos2 - y_vector_pos1)**2 + (x_vector_pos2 - x_vector_pos1)**2)**0.5  # Strecke zwischen Position 1 und 2
    # print("Distanz zu Positon 2: ", distance_p1_p2)
    # robot.behavior.drive_straight(distance_mm(distance_p1_p2), speed_mmps(500)) # Vector fährt zu Position 2
    # print("driving")

    # turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) # Berechenen des Winkels um den sich Vector drehen muss (Position 2)
    # print("Turning-Angle zum Tor: ", turning_angel)
    # robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich auf Position 2

    pose = Pose(x=(x_vector_pos2 - env._POSITION_START_X), y=(y_vector_pos2 - env._POSITION_START_Y), z=0, angle_z=degrees(0))
    robot.behavior.go_to_pose(pose)

    turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) # Berechenen des Winkels um den sich Vector drehen muss (Position 2)
    print("Turning-Angle zum Tor: ", turning_angel)
    robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich auf Position 1
    time.sleep(0.2)
    if perception.current_rotation_to_ball() is not None:
        robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball

    shooting(env, robot)  # Vector fährt zum Ball und schießt


def play_defensive(env, robot):
    '''Vector fährt 5cm vor eigenes Tor und dreht sich Richtung Ball
    '''
    print("Rotation Vector: ", env.self.rotation)
    print("play_defensive()")
    x_ball = env.ball.position_x
    y_ball = env.ball.position_y
    print("Positon Ball: x = ", x_ball, "; y = ",  y_ball)

    # # Zum Tor fahren
    # turning_angel = turning_angel_vector(env, (x_goal_self), y_goal_self) # Berechnen des Winkel um den sich Vector zum eigenen Tor drehen muss 
    # print("Turning-Angle zum Tor: ", turning_angel)
    # robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich zum eigenen Tor
    # y_vector = env.self.position_y
    # x_vector = env.self.position_x
    # distance_to_goal = ((y_vector - y_goal_self)**2 + (x_vector - (x_goal_self))**2)**0.5  # Strecke zwischen Vector und eigenem Tor
    # print("Distanz zum eigenen Tor ", distance_to_goal)
    # robot.behavior.drive_straight(distance_mm(distance_to_goal), speed_mmps(500))  # Vector fährt zum eigenen Tor
    # print("Fahre zum Tor")
    # turning_angel = turning_angel_vector(env, x_ball, y_ball) # Berechnen des Winkel um den sich Vector zur letzten bekannten Positon des Balls drehen muss 
    # print("Turning-Angle zum Ball: ", turning_angel)
    # robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich zur letzten bekannten Postion des Balls
    
    pose = Pose(x=(0 - env._POSITION_START_X), y=(500 - env._POSITION_START_Y), z=0, angle_z=degrees(0))
    robot.behavior.go_to_pose(pose)

def turning_angel_vector(env, endposition_x, endposition_y):
    '''Berechnet Winkel, um den sich Vector auf der Stelle drehen muss,
    um danach auf einer Gerade vom aktuellen Standort zur Endposition zu fahren.
    '''
    startpositon_y = env.self.position_y
    print("startpos-y = ", startpositon_y)
    startpositon_x = env.self.position_x
    print("startpos-x = ", startpositon_x)
    countered_leg = endposition_y - startpositon_y  # Gegenkathete
    adjacent_leg = endposition_x - startpositon_x  # Ankathete
    angle_rad_pos2 = math.atan2(countered_leg, adjacent_leg)  # Winkel zwischen x-Achse und Gerade zwischen Postion 1 und 2 (Bogenmaß)
    angle_deg_pos2 = math.degrees(angle_rad_pos2)  # Winkel in Grad

    # Berechenen des winkels um den sich Vector drehen muss
    if angle_deg_pos2 < 0:
        angle_deg_pos2 = 360 + angle_deg_pos2  # eventuell Umwandlung in positiven Winkel
    
    angle_deg_vector = env.self.rotation  # aktuelle Rotation des Vectors
    if angle_deg_vector < 0:
        angle_deg_vector = 360 + angle_deg_vector  # umwandlung von negativen in positiven Winkel
    turning_angle = 360 - angle_deg_vector + angle_deg_pos2  # Berechenen des Winkels um den sich Vector drehen muss

    if turning_angle > 360:
        turning_angle = turning_angle - 360  # Winkel nicht größer als 360 Grad
    
    if turning_angle > 180:
        turning_angle = turning_angle - 360  # Drehung nicht mehr als 180 Grad

    return turning_angle



def distance_average(env, robot):
    '''Berechnung für den Abstand zum Ball,
    basierend auf der Infrarot-Messung und der 
    approximierten Berechnung über die Kamera
    '''
    unobstructed = robot.proximity.last_sensor_reading.unobstructed
    if not unobstructed:
        distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
        print("Distanz zu Ball infrarot: ", distance_to_ball)
    
        # approximierte Distanz:
        difference_x = env.self.position_x - env.ball.position_x
        difference_y = env.self.position_y - env.ball.position_y
        distance_to_ball_approx = ((difference_x**2 + difference_y**2)**0.5)
        print("Distanz zu Ball approximiert: ", distance_to_ball_approx)

        diffrence_infra_approx = abs(distance_to_ball - distance_to_ball_approx) # Unterschied zwischen beiden berechneten Abständen
        if (diffrence_infra_approx < 10 ): # Wenn unterschied nicht größer als 1 cm, mittelwert aus infrarot und approximierten Abstand zu Ball
            distance_to_ball = ((distance_to_ball + distance_to_ball_approx)/2)
        print("Distanz zu Ball : ", distance_to_ball)
        return distance_to_ball
    
    else:
        print("Abstand konnte nicht berechnet werden")
        return -1


def shooting(env, robot):
    ''' Vector fährt auf Ball zu, korregiert eventuell Fahrtrichtung.
    Ist er nah genug am Ball, soll er mit Hilfe seines Lifts schießen.
    (Auf Threads basierend)
    '''
    print("shooting()")
    
    robot.behavior.set_lift_height(1)
    if perception.current_rotation_to_ball() is not None:
        robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
        time.sleep(0.1)
    

    distance_to_ball = distance_average(env, robot)
    
    if distance_to_ball is not -1:
        robot.behavior.drive_straight(distance_mm(distance_to_ball-18), speed_mmps(500))
        robot.behavior.set_lift_height(0.0, accel=1000.0, max_speed=1000.0, duration=0.0)
        print("shot")
        
        time.sleep(0.2)

        if perception.current_rotation_to_ball() is not None:
            robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
        
        distance_to_ball = distance_average(env, robot)
        
        while (distance_to_ball < 100 and distance_to_ball >= 0): #falls der Ball nicht richtig geschossen wurde, wird es nochmal versucht
            if distance_to_ball is not -1:
                robot.behavior.set_lift_height(1.0, accel=1000.0, max_speed=1000.0, duration=0.0)
                robot.behavior.drive_straight(distance_mm(distance_to_ball-18), speed_mmps(500))
                robot.behavior.set_lift_height(0.0, accel=1000.0, max_speed=1000.0, duration=0.0)
                print("shot")
            
                time.sleep(0.2)

                if perception.current_rotation_to_ball() is not None:
                    robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            
                distance_to_ball = distance_average(env, robot)

        print("vorbei")
    

   
