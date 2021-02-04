import math
import perception
import time
import random
import threading
from anki_vector.util import degrees, distance_mm, speed_mmps
import main


x_goal_enemy = 1500
y_goal_enemy = 500
x_goal_self = 0
y_goal_self = 500


def look_for_ball(env, robot):
    '''Vector dreht sich und sucht nach Ball
    '''
    print("look_for_ball()")
    ball_is_seen = env.ball.is_seen()
    degrees_turned = 0
    while not ball_is_seen and not (degrees_turned == 360):
        robot.behavior.turn_in_place(degrees(45))
        degrees_turned = degrees_turned + 45
        ball_is_seen = env.ball.is_seen()
        if ball_is_seen:
            time.sleep(0.2)

    if (degrees_turned == 360) and not ball_is_seen:
        print("ball not found")
        play_defensive(env, robot)
    else:
        print("ball found")
        if perception.current_rotation_to_ball() is not None:
            # Vector dreht sich zum Ball
            robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball()))
        else:
            # Falls Vector sich zu weit gedreht hat
            robot.behavior.turn_in_place(degrees(-45))
            time.sleep(0.1)
            if perception.current_rotation_to_ball() is not None:
                # Vector dreht sich zum Ball
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball()))
        time.sleep(0.1)  # Verzögerung Kamera-Feed ausgleichen
        play_ball(env, robot)


def play_ball(env, robot):
    '''Entscheidet, ob Vector offensiv oder defensiv spielen soll.
    '''
    print("play_ball()")
    if ((env.self.rotation < 90) & (env.self.rotation > -90)):
        play_offensive(env, robot)
    else:
        play_defensive(env, robot)


def play_offensive(env, robot):
    '''Fährt zum Ball, und führt passenden Spielzug aus.
    '''
    print("play_offensive()")
    ball_is_seen = env.ball.is_seen()
    distance_to_ball = distance_average(env, robot)
    unobstructed = robot.proximity.last_sensor_reading.unobstructed

    while ball_is_seen and (unobstructed or (distance_to_ball > 95)):
        # Vector soll bis 8 cm auf den Ball zufahren
        if ((distance_to_ball > 150) and ((x_goal_enemy - env.self.position_x) > 150)):
            print("ball weiter als 15cm entfernt: ", distance_to_ball)
            #driving_distance = -50 + 0.83 * distance_to_ball
            driving_distance = distance_to_ball - 50
            if driving_distance > 500:
                driving_distance = 500
            if driving_distance > (x_goal_enemy - env.self.position_x):
                 # Falls vector gegen Bande fahren würde
                driving_distance = (x_goal_enemy - env.self.position_x) 
            print("driving_distance:" , driving_distance)
            robot.behavior.drive_straight(distance_mm(driving_distance), speed_mmps(500))
            turning_angel = perception.current_rotation_to_ball()
            if turning_angel is not None and abs(turning_angel) > 5:
                # Vector dreht sich zum Ball
                robot.behavior.turn_in_place(degrees(turning_angel))
                
        else:
            print("ball weniger als 15cm entfernt", distance_to_ball)
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball()))
            driving_distance = distance_to_ball - 75
            if driving_distance < 19:
                driving_distance = 0
            robot.behavior.drive_straight(distance_mm(driving_distance), speed_mmps(500))
        unobstructed = robot.proximity.last_sensor_reading.unobstructed
        
        difference_x = env.self.position_x - env.ball.position_x
        difference_y = env.self.position_y - env.ball.position_y
        distance_to_ball = ((difference_x**2 + difference_y**2)**0.5)

        ball_is_seen = env.ball.is_seen()

    ball_is_seen = env.ball.is_seen()

    if ball_is_seen:
        time.sleep(0.1)
        do_play_move(env, robot)
       

def play_defensive(env, robot):
    '''Vector fährt 5cm vor eigenes Tor und dreht sich Richtung Ball
    '''
    print("play_defensive()")
    x_ball = env.ball.position_x
    y_ball = env.ball.position_y
    print("Positon Ball: x = ", x_ball, "; y = ",  y_ball)

    # Zum Tor fahren
    turning_angel = turning_angel_vector(env, (x_goal_self), y_goal_self) # Berechnen des Winkel um den sich Vector zum eigenen Tor drehen muss 
    robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich zum eigenen Tor
    time.sleep(0.3)
    ball_is_seen = env.ball.is_seen()
    rotation_to_ball = perception.current_rotation_to_ball()
    if rotation_to_ball is None:
        rotation_to_ball = 90
    ball_in_line = ball_is_seen and abs(rotation_to_ball) < 40

    while ball_in_line:   # überprüfen ob Ball im weg ist
        # approximierte Distanz:
        difference_x = env.self.position_x - env.ball.position_x
        difference_y = env.self.position_y - env.ball.position_y
        distance_to_ball_approx = ((difference_x**2 + difference_y**2)**0.5)
        print("distance_to_ball_approx", distance_to_ball_approx)

        if distance_to_ball_approx > 100:
            robot.behavior.drive_straight(distance_mm(distance_to_ball_approx-50), speed_mmps(500))
        time.sleep(0.2)
        ball_is_seen = env.ball.is_seen()
        if perception.current_rotation_to_ball() is not None:
            rotation_to_ball = perception.current_rotation_to_ball()
        if ball_is_seen and (abs(rotation_to_ball) < 25):
            if rotation_to_ball < 0: # nach links drehen
                turning_angel = turning_angel_vector(env, (env.self.position_x), 0)
                if turning_angel > 45:
                    turning_angel = turning_angel - 45
                robot.behavior.turn_in_place(degrees(turning_angel)) 
                robot.behavior.drive_straight(distance_mm(90), speed_mmps(500))  # Vector fährtnach links
            else:
                turning_angel = turning_angel_vector(env, (env.self.position_x), 1000)
                if turning_angel < -45:
                    turning_angel = turning_angel + 45
                robot.behavior.turn_in_place(degrees(turning_angel)) 
                robot.behavior.drive_straight(distance_mm(90), speed_mmps(500))  # Vector fährt nach rechts
            turning_angel = turning_angel_vector(env, (x_goal_self), y_goal_self) # Berechnen des Winkel um den sich Vector zum eigenen Tor drehen muss 
            print("Turning-Angle zum Tor: ", turning_angel)
            robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich zum eigenen Tor
            time.sleep(0.3)
            ball_is_seen = env.ball.is_seen()
            rotation_to_ball = perception.current_rotation_to_ball()
            ball_in_line = ball_is_seen and rotation_to_ball is not None
        
        else:
            ball_in_line = False

    y_vector = env.self.position_y
    x_vector = env.self.position_x
    distance_to_goal = ((y_vector - y_goal_self)**2 + (x_vector - (x_goal_self))**2)**0.5  # Strecke zwischen Vector und eigenem Tor
    print("Distanz zum eigenen Tor ", distance_to_goal)
    robot.behavior.drive_straight(distance_mm(distance_to_goal), speed_mmps(500))  # Vector fährt zum eigenen Tor
    print("Fahre zum Tor")
    turning_angel = turning_angel_vector(env, 500, 500) 
    robot.behavior.turn_in_place(degrees(turning_angel))
    
    # Verteidigung im Tor:
    # Vector sucht in einem 180° Winkel vor ihm
    # findet er ihn nicht, fährt er 20cm vor und sucht analog (insgesamt 3x)
    # hat er ihn gefunden, wird play_offensive() aufgerufen
    # andernfalls wird look_for_ball() aufgerufen
    time.sleep(1) # verzögerung kamera-feed ausgleichen
    ball_is_seen = env.ball.is_seen()
    if not ball_is_seen:
        robot.behavior.turn_in_place(degrees(-45))
        time.sleep(0.1) # Verzögerung Kamera-Feed ausgleichen
        ball_is_seen = env.ball.is_seen()
    else:
        turning_angel = perception.current_rotation_to_ball()
        if turning_angel is not None:
                # Vector dreht sich zum Ball
                robot.behavior.turn_in_place(degrees(turning_angel))
    i = 0
    while not ball_is_seen and (i < 3):
        
        robot.behavior.turn_in_place(degrees(90))
        time.sleep(0.2) # Verzögerung Kamera-Feed ausgleichen
        ball_is_seen = env.ball.is_seen()
        if not ball_is_seen:
            robot.behavior.turn_in_place(degrees(-45))
            time.sleep(0.2) # Verzögerung Kamera-Feed ausgleichen
            ball_is_seen = env.ball.is_seen()
            if not ball_is_seen:
                robot.behavior.drive_straight(distance_mm(200), speed_mmps(500))
                time.sleep(0.2) # Verzögerung Kamera-Feed ausgleichen
                ball_is_seen = env.ball.is_seen()
                if not ball_is_seen:
                    robot.behavior.turn_in_place(degrees(-45))
                    time.sleep(0.2) # Verzögerung Kamera-Feed ausgleichen
                    ball_is_seen = env.ball.is_seen()
        i = i + 1
    if ball_is_seen:
        play_offensive(env, robot)
    else:
        look_for_ball(env, robot)


def turning_angel_vector(env, endposition_x, endposition_y):
    '''Berechnet Winkel, um den sich Vector drehen muss, um sich zur Endposition auszurichten.
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
    pointing_to_wall = False #wenn vector auf wand schaut darf er nicht mit dem infrarot messen
    if (env.self.position_y > (env._FIELD_LENGTH_Y-200)) and env.self.rotation > 10 and env.self.rotation < 170:
        pointing_to_wall = True
    if (env.self.position_y < (200)) and env.self.rotation > -170 and env.self.rotation < -10:
        pointing_to_wall = True
    ball_is_seen = env.ball.is_seen()
    if not unobstructed and not pointing_to_wall:
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
    
    elif ball_is_seen:
        difference_x = env.self.position_x - env.ball.position_x
        difference_y = env.self.position_y - env.ball.position_y
        distance_to_ball_approx = ((difference_x**2 + difference_y**2)**0.5)
        print("Distanz zu Ball approximiert: ", distance_to_ball_approx)
        return distance_to_ball_approx
    else:
        return -1


def shooting(env, robot):
    ''' Vector fährt auf Ball zu, korregiert eventuell Fahrtrichtung.
    Ist er nah genug am Ball, soll er mit Hilfe seines Lifts schießen.
    '''
    print("shooting()")
    ball_is_seen = env.ball.is_seen()
    if ball_is_seen:
        robot.behavior.set_lift_height(1)
        if perception.current_rotation_to_ball() is not None:
            robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            time.sleep(0.2) # Verzögerung Kamera-Feed ausgleichen

        # Vector soll in Schussdistanz zum Ball fahren
        distance_to_ball = distance_average(env, robot)
        unobstructed = robot.proximity.last_sensor_reading.unobstructed
        if not unobstructed:
            distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
            print("Distanz zu Ball infrarot: ", distance_to_ball)
            if distance_to_ball < 90:
                robot.behavior.drive_straight(distance_mm(distance_to_ball-20), speed_mmps(500))
            else:
                difference_x = env.self.position_x - env.ball.position_x
                difference_y = env.self.position_y - env.ball.position_y
                distance_to_ball = ((difference_x**2 + difference_y**2)**0.5)
                if distance_to_ball > 80:
                    robot.behavior.drive_straight(distance_mm(distance_to_ball-8), speed_mmps(500))
                elif distance_to_ball > 50:
                    robot.behavior.drive_straight(distance_mm(distance_to_ball-18), speed_mmps(500))
                else:
                    robot.behavior.drive_straight(distance_mm(distance_to_ball-30), speed_mmps(500))
        elif distance_to_ball is not -1:  # falls infrarot nicht funktioniert
            if distance_to_ball > 80:
                robot.behavior.drive_straight(distance_mm(distance_to_ball-8), speed_mmps(500))
            elif distance_to_ball > 50:
                robot.behavior.drive_straight(distance_mm(distance_to_ball-18), speed_mmps(500))
            else:
                robot.behavior.drive_straight(distance_mm(distance_to_ball-30), speed_mmps(500))
        robot.behavior.set_lift_height(0.0, accel=1000.0, max_speed=1000.0, duration=0.0)
        print("shot")
            
        time.sleep(0.6) # Ball wegrollen lassen

        if perception.current_rotation_to_ball() is not None:
            robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
        
        distance_to_ball = distance_average(env, robot)
        ball_is_seen = env.ball.is_seen()
        if (env.self.position_y > (env._FIELD_LENGTH_Y-100) or env.self.position_y < 100):
            while (distance_to_ball < 100 and distance_to_ball >= 0 and ball_is_seen):  # falls der Ball nicht richtig geschossen wurde, wird es nochmal versucht
                if distance_to_ball is not -1:
                    robot.behavior.set_lift_height(1.0, accel=1000.0, max_speed=1000.0, duration=0.0)
                    robot.behavior.drive_straight(distance_mm(distance_to_ball-18), speed_mmps(500))
                    robot.behavior.set_lift_height(0.0, accel=1000.0, max_speed=1000.0, duration=0.0)
                    print("shot")
                
                    time.sleep(0.4) # Ball wegrollen lassen

                    if perception.current_rotation_to_ball() is not None:
                        robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
                
                    distance_to_ball = distance_average(env, robot)
                ball_is_seen = env.ball.is_seen()
            time.sleep(0.5)
        ball_is_seen = env.ball.is_seen()
        if ball_is_seen:
            print("ball_x: ", env.ball.position_x)
            # Torjubel nach geschossenem Tor:
            if env.ball.position_x > x_goal_enemy:
                main.main.ball_in_goal = True
                torsoundThread = threading.Thread(target=torsound, args=[robot])
                torsoundThread.start()
                robot.behavior.set_lift_height(1.0)
                robot.behavior.turn_in_place(degrees(360))
                robot.behavior.turn_in_place(degrees(-360))
                robot.behavior.turn_in_place(degrees(360))
                robot.behavior.turn_in_place(degrees(-360))
                robot.behavior.set_lift_height(0)
                


def get_ball_position(env, robot):
    
    print("get_ball_position")
    # Koordinaten vom Ball bestimmen
    if perception.current_rotation_to_ball() is not None:
        robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball()))
    distance_to_ball = distance_average(env, robot)
    unobstructed = robot.proximity.last_sensor_reading.unobstructed
    if not unobstructed: # wenn möglich nur infrarot
        distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm

    x_vector = env.self.position_x
    y_vector = env.self.position_y
    print("x-postion vetor akutell : ", x_vector)
    print("y-postion vektor aktuell: ", y_vector)
    rotation_vector = env.self.rotation
    x_ball = x_vector + math.cos(math.radians(rotation_vector))*(distance_to_ball + 35)
    y_ball = y_vector + math.sin(math.radians(rotation_vector))*(distance_to_ball + 35)
    time.sleep(0.2)
    print("Infrarot Positon Ball: x = ", x_ball, "; y = ",  y_ball)
    ball_position = [x_ball, y_ball, x_vector, y_vector]
    return ball_position


def calculate_shot_position(env, robot, x_ball, y_ball, distance_to_ball=70):
    # Berechnung des Richtungsvektors
    x_direction = 1
    y_direction = (y_goal_enemy - y_ball)/(x_goal_enemy - x_ball)

    # Normieren des Richtungsvektors
    abs_value = ((x_direction**2)+(y_direction**2))**0.5  # Betrag des Vectors
    x_direction_norm = (1/abs_value)*x_direction
    y_direction_norm = (1/abs_value)*y_direction

    # Berechnen der Koordinaten des Punktes [2] 7 cm hinter dem Ball, in
    # Verlängerung zur Schussbahn, zu dem Vector fahren soll.
    x_vector_pos2 = -distance_to_ball * x_direction_norm + x_ball
    y_vector_pos2 = -distance_to_ball * y_direction_norm + y_ball
    print("Neu brechnete Position Vector: x = ", x_vector_pos2, " y = ",y_vector_pos2)
    shot_position = [x_vector_pos2, y_vector_pos2]
    return shot_position


def drive_to_position(env, robot, x_vector_pos2, y_vector_pos2):
    robot.behavior.set_lift_height(1)
    turning_angel = turning_angel_vector(env, x_vector_pos2, y_vector_pos2) # Berechenen des Winkels um den sich Vector drehen muss (Positon 1)
    print("Turning-Angle zur Position 2: ", turning_angel)
    robot.behavior.turn_in_place(degrees(turning_angel))  # Vector dreht sich auf Position 1
    print("turning")

    y_vector_pos1 = env.self.position_y
    x_vector_pos1 = env.self.position_x
    distance_p1_p2 = ((y_vector_pos2 - y_vector_pos1)**2 + (x_vector_pos2 - x_vector_pos1)**2)**0.5  # Strecke zwischen Position 1 und 2
    print("Distanz zu Positon 2: ", distance_p1_p2)
    robot.behavior.drive_straight(distance_mm(distance_p1_p2), speed_mmps(500))  # Vector fährt zu Position 2
    print("driving")

def torsound(robot):
    '''Vector spielt zufaelligen Torjubel ab
    '''
    number = random.random() * 5
    if number > 4:
        robot.audio.stream_wav_file('audio/torsound.wav', volume=100)
    elif number > 3:
        robot.audio.stream_wav_file('audio/champions.wav', volume=100)
    elif number > 2:
        robot.audio.stream_wav_file('audio/doepdoep.wav', volume=100)
    elif number > 1:
        robot.audio.stream_wav_file('audio/samba.wav', volume=100)
    else:
        robot.audio.stream_wav_file('audio/sieger.wav', volume=100)

def do_play_move(env, robot):

    ball_position = get_ball_position(env, robot)
    x_ball = ball_position[0]
    y_ball = ball_position[1]
    y_vector = ball_position[3]

    ball_in_deadspot = False
    # Ueberpruefen, ob Ball im "toten Winkel"- Dreieck mit den Eckpunkten
    # (1000/1000), (1500/1000) und (1500/600) liegt
    if ((y_ball > 600) and (x_ball > 1000)):
        if (y_ball > (-0.8 * x_ball + 1800)):
            print("Ball im oberen Toten Winkel")
            ball_in_deadspot = True

    # Ueberpruefen, ob Ball im "toten Winkel"- Dreieck mit den Eckpunkten 
    # (1000/0), (1500/0) und (1500/400) liegt
    if ((y_ball < 400) and (x_ball > 1000)):
        if (y_ball < (0.8 * x_ball - 800)):
            print("Ball im unteren Toten Winkel")
            ball_in_deadspot = True
    
    if ball_in_deadspot:
        robot.behavior.set_lift_height(1)
        x_vector_pos2 = x_ball -10
        y_vector_pos2 = 0
        if y_ball > 600:
            y_vector_pos2 = y_ball + 100
        else:
            y_vector_pos2 = y_ball - 100
        # Vector fährt zu pos2
        if (x_vector_pos2 > x_goal_enemy) or (y_vector_pos2 > 960) or (y_vector_pos2 < 40):
            # falls schussposition ausserhalb des spielfelds ist
            shooting(env, robot)
        else:
            drive_to_position(env, robot, x_vector_pos2, y_vector_pos2)
            turning_angel = turning_angel_vector(env, env.self.position_x, y_goal_enemy)
            robot.behavior.turn_in_place(degrees(turning_angel))

            # vector fährt mit ball vors tor
            robot.behavior.set_lift_height(0)
            time.sleep(0.1)
            if perception.current_rotation_to_ball() is not None:
                # vector dreht sich zum Ball
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball()))
            time.sleep(0.1)
            # if perception.current_rotation_to_ball() is not None:
            #     # vector dreht sich zum Ball
            #     robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball()))
            robot.behavior.drive_straight(distance_mm(abs(env.self.position_y - y_goal_enemy)-60), speed_mmps(80))

            # vector fährt zu seiner schuss-position
            robot.behavior.drive_straight(distance_mm(-50), speed_mmps(500))
        
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            time.sleep(0.1)
            ball_position = get_ball_position(env, robot)
            x_ball = ball_position[0]
            y_ball = ball_position[1]
        
            shot_position = calculate_shot_position(env, robot, x_ball, y_ball, distance_to_ball=80)
            x_vector_pos2 = shot_position[0]
            y_vector_pos2 = shot_position[1]
            
            drive_to_position(env, robot, x_vector_pos2, y_vector_pos2)
            
            turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) # Berechenen des Winkels um den sich Vector zum Tor drehen muss
            print("Turning-Angle zum Tor: ", turning_angel)
            robot.behavior.turn_in_place(degrees(turning_angel))  # Vector dreht sich zum Tor

            time.sleep(0.1)
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            time.sleep(0.2)
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            distance_to_enemy_goal = ((env.self.position_x - x_goal_enemy)**2+(env.self.position_y - y_goal_enemy)**2)**0.5 # Abstand zu gegnerischem Tor

            shooting(env, robot)

    else:  # Ball nicht im toten Winkel
        shot_position = calculate_shot_position(env, robot, x_ball, y_ball)
        x_vector_pos2 = shot_position[0]
        y_vector_pos2 = shot_position[1]
        y_diffrence_pos_1_2 = abs(y_vector - y_vector_pos2)
        
        if (y_vector_pos2 > (env._FIELD_LENGTH_Y-50) or y_vector_pos2 < 50):
            # berechnete Position 2 fuer Vector nicht erreichbar, Schuss ueber Bande
            shooting(env, robot)  
            turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) 
            robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich zum Tor
            time.sleep(0.2)

        elif y_diffrence_pos_1_2 < 20:
            # Unterschied zur neuen Position nicht zu groß, Vector soll einfach schiessen
            shooting(env, robot)  

        else:  
            # Vector faehrt er zur berechneten Position 2 und schiesst
            drive_to_position(env, robot, x_vector_pos2, y_vector_pos2)
            # Berechenen des Winkels um den sich Vector drehen muss (Position 2):
            turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) 
            # Vector dreht sich auf Position 2:
            robot.behavior.turn_in_place(degrees(turning_angel))
            
            time.sleep(0.1)
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            time.sleep(0.2)
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            distance_to_enemy_goal = ((env.self.position_x - x_goal_enemy)**2+(env.self.position_y - y_goal_enemy)**2)**0.5 # Abstand zu gegnerischem Tor

            if distance_to_enemy_goal > 500:
                # falls vector weiter als 50cm vom gegnerischen Tor entfernt ist,
                # soll er denn ball bis 40cm vor das tor führen und dann schiessen
                robot.behavior.set_lift_height(0)
                robot.behavior.drive_straight(distance_mm(distance_to_enemy_goal-400), speed_mmps(100))
                robot.behavior.drive_straight(distance_mm(-40), speed_mmps(500))
                ball_is_seen = env.ball.is_seen()
                if ball_is_seen:
                    # vector soll eventuell schussposition neu berechnen
                    time.sleep(0.2)
                    ball_position = get_ball_position(env, robot)
                    x_ball = ball_position[0]
                    y_ball = ball_position[1]
                    y_vector = ball_position[3]

                    shot_position = calculate_shot_position(env, robot, x_ball, y_ball)
                    x_vector_pos2 = shot_position[0]
                    y_vector_pos2 = shot_position[1]
                    y_diffrence_pos_1_2 = abs(y_vector - y_vector_pos2)
                    # falls unterschied zur neuen position zu groß ist, soll vector zu neuen position fahren
                    if y_diffrence_pos_1_2 > 20:
                        drive_to_position(env, robot, x_vector_pos2, y_vector_pos2)
                        turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) # Berechenen des Winkels um den sich Vector drehen muss (Position 2)
                        print("Turning-Angle zum Tor: ", turning_angel)
                        robot.behavior.turn_in_place(degrees(turning_angel))  # Vector dreht sich zum Tor
                        time.sleep(0.1)
                        if perception.current_rotation_to_ball() is not None:
                            robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
                        time.sleep(0.2)
                        if perception.current_rotation_to_ball() is not None:
                            robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
        
            shooting(env, robot)  # Vector fährt zum Ball und schießt

    