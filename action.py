
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
            robot.behavior.drive_straight(distance_mm(300), speed_mmps(500))
            degrees_turned = 0
        robot.behavior.turn_in_place(degrees(60))
        degrees_turned = degrees_turned + 60
        ball_is_seen = env.ball.is_seen()
    print("ball found")
    print("Rotation Vector: ", env.self.rotation)
    #print(perception.current_rotation_to_ball())
    #robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
    #print("turn to ball")
    play_ball(env, robot)
    

def play_ball(env, robot):
    '''Entscheidet, ob Vector offensiv oder defensiv spielen soll.
    (Ball zwischen gegnerischem Tor und Vector => offensiv)
    (Vector zwischen gegnerischem Tor und Ball => defensiv)
    '''
    print("play_ball()")
    if ((env.self.rotation < 125) & (env.self.rotation > -115)):
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
    if not unobstructed:
        distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
    while unobstructed or (distance_to_ball > 200):  # Vector soll bis 20cm vor dem ball gerade auf ihn zufahren
        # robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
        robot.behavior.drive_straight(distance_mm(40), speed_mmps(500))
        if not unobstructed:
            distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm

    # Koordinaten vom Ball bestimmen
    # robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
    distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
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

    # Berechnen der Koordinaten des Punktes [2] 10cm hinter dem Ball, in
    # Verlängerung zur Schussbahn, zu dem Vector fahren soll.
    x_vector_pos2 = -100 * x_direction_norm + x_ball
    y_vector_pos2 = -100 * y_direction_norm + y_ball
    print("Neu brechnete Position Vector: x = ", x_vector_pos2 , " y = ", y_vector_pos2)

    # Vector fährt von Positon 1 (aktuell) zur Position 2
    '''eventuell mit go_to_pose(pose)'''

    turning_angel = turning_angel_vector(env, x_vector_pos2, y_vector_pos2) # Berechenen des Winkels um den sich Vector drehen muss (Positon 1)
    print("Turning-Angle zur Position 2: ", turning_angel)
    robot.behavior.turn_in_place(degrees(turning_angel))  # Vector dreht sich auf Position 1
    print("turning")

    y_vector_pos1 = env.self.position_y
    x_vector_pos1 = env.self.position_x
    distance_p1_p2 = ((y_vector_pos2 - y_vector_pos1)**2 + (x_vector_pos2 - x_vector_pos1)**2)**0.5  # Strecke zwischen Position 1 und 2
    print("Distanz zu Positon 2: ", distance_p1_p2)
    robot.behavior.drive_straight(distance_mm(distance_p1_p2), speed_mmps(500)) # Vector fährt zu Position 2
    print("driving")

    turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) # Berechenen des Winkels um den sich Vector drehen muss (Position 2)
    print("Turning-Angle zum Tor: ", turning_angel)
    robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich auf Position 1

    # shooting(env, robot)  # Vector fährt zum Ball und schießt


def play_defensive(env, robot):
    '''Vector fährt 5cm vor eigenes Tor und dreht sich Richtung Ball
    '''
    print("Rotation Vector: ", env.self.rotation)
    print("play_defensive()")
    x_ball = env.ball.position_x
    y_ball = env.ball.position_y
    print("Positon Ball: x = ", x_ball, "; y = ",  y_ball)

    # Zum Tor fahren
    turning_angel = turning_angel_vector(env, (x_goal_self), y_goal_self) # Berechnen des Winkel um den sich Vector zum eigenen Tor drehen muss 
    print("Turning-Angle zum Tor: ", turning_angel)
    robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich zum eigenen Tor
    y_vector = env.self.position_y
    x_vector = env.self.position_x
    distance_to_goal = ((y_vector - y_goal_self)**2 + (x_vector - (x_goal_self))**2)**0.5  # Strecke zwischen Vector und eigenem Tor
    print("Distanz zum eigenen Tor ", distance_to_goal)
    robot.behavior.drive_straight(distance_mm(distance_to_goal), speed_mmps(500))  # Vector fährt zum eigenen Tor
    print("Fahre zum Tor")
    turning_angel = turning_angel_vector(env, x_ball, y_ball) # Berechnen des Winkel um den sich Vector zur letzten bekannten Positon des Balls drehen muss 
    print("Turning-Angle zum Ball: ", turning_angel)
    robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich zur letzten bekannten Postion des Balls
    

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


def shooting(env, robot):
    ''' Vector fährt auf Ball zu, korregiert eventuell Fahrtrichtung.
    Ist er nah genug am Ball, soll er mit Hilfe seines Lifts schießen.
    (Auf Threads basierend)
    '''
    print("shooting()")
    # Events zur Kommunikation zwischen den Threads
    ball_is_in_line = threading.Event()
    shoot_ball = threading.Event()

    def ball_still_in_line(robot):
        ''' Methode die als Thread ausgeführt wird.
        Prüft ob Vector noch auf den Ball zufährt und korrigiert
        gegebenfalls die Richtung
        '''
        print("ball_still_in_line().start")
        ball_is_in_line.set()
        while not shoot_ball.is_set():
            pic = support_functions.take_picture_to_byte(robot)
            poi = perception.detect_object(robot, "online", pic)
            if poi > 0.55:
                ball_is_in_line.clear()
                correction_angle = (45-(poi*2)*45)  # Winkel um den korrigiert wird
                print("Korrektur um ", correction_angle, " Grad")
                robot.behavior.turn_in_place(degrees(correction_angle))
                ball_is_in_line.set()
            elif poi < 0.45:
                ball_is_in_line.clear()
                correction_angle = ((poi-0.5) * -45)  # Winkel um den korrigiert wird
                print("Korrektur um ", correction_angle, " Grad")
                robot.behavior.turn_in_place(degrees(correction_angle))
                ball_is_in_line.set()

    def drive_and_shoot(env, robot):
        '''Methode die als Thread ausgeführt wird.
        Fährt gerade aus und activiert das shoot_ball-Event
        sobald sie nah genug am Ball ist.
        '''
        print("drive_and_shoot().start")
        shoot_ball.clear()
        while ball_is_in_line.is_set():
            
            # Berechnung für den Abstand zwischen Vector und Ball

            distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
            
            # alternativ:
            # difference_x = env.self.position_x - env.ball.position_x
            # difference_y = env.self.position_y - env.ball.position_y
            # distance_to_ball = ((difference_x**2 + difference_y**2)**0.5)

            if distance_to_ball > 35:
                robot.behavior.drive_straight(distance_mm(5), speed_mmps(500))
            elif distance_to_ball <= 35:
                print("Ball ins Schussweite")
                shoot_ball.set()
                robot.behavior.drive_straight(distance_mm(40), speed_mmps(500))
                shoot_ball.clear()
                ball_is_in_line.clear()

    def shoot(robot):
        '''Methode die als Thread ausgeführt wird.
        bewegt lift des Vectors auf und ab'''
        print("shoot().start")
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

    drive_and_shootThread.join()
    ball_still_in_lineThread.join()
    shootThread.join()

def main():
    
    args = anki_vector.util.parse_command_args()
    with anki_vector.Robot(args.serial) as robot:
        env = environment.Environment(robot,
                                      field_length_x=2000.0,
                                      field_length_y=1000.0,
                                      goal_width=200.0,
                                      ball_diameter=40.0,
                                      position_start_x=100.0,
                                      position_start_y=500.0,
                                      enable_environment_viewer=False)
        print("Zum Starten Enter drücken")
        wait_until_enter = input()
        print("Goooooo")
        print("postion anfang: ", env.self.position_x)
        print("postion anfang: ", env.self.position_y)
        
        print("detect_object()")
        #perception.detect_ball(robot, env)
        look_for_ball(env, robot)
        print("position Ende: ", env.self.position_x)
        print("position Ende: ", env.self.position_y)


if __name__ == "__main__":
    main()

