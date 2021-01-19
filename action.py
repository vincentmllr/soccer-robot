# import environment
import math
import perception
# import support_functions
# import anki_vector
# import anki_vector.util
# import threading
import time
from anki_vector.util import degrees, distance_mm, speed_mmps, Pose

x_goal_enemy = 1500
y_goal_enemy = 500
x_goal_self = 0
y_goal_self = 500


def look_for_ball(env, robot):
    '''Vector dreht sich so lange bis er Ball gefunden hat,
    ruft dann play_ball auf. Falls er ihn nach einer 360° Drehung
    nicht gefunden hat, wird play_defensive() aufgerufen.

    :param env: Enviroment-Objekt
    :param robot: anki_vector.Robot-Objekt
    '''
    print("look_for_ball()")
    ball_is_seen = env.ball.is_seen()
    degrees_turned = 0
    while not ball_is_seen and not (degrees_turned == 360):

        robot.behavior.turn_in_place(degrees(45))
        degrees_turned = degrees_turned + 45
        print(env.self.rotation)
        ball_is_seen = env.ball.is_seen()
    if (degrees_turned == 360) and not ball_is_seen:
        print("Ball not found")
        play_defensive(env, robot)
        degrees_turned = 0
    else:
        print("ball found")
        print("Rotation Vector: ", env.self.rotation)

        time.sleep(0.1)  # Verzögerung Kamera-Feed ausgleichen
        print("wake up")
        print("Rotation to Ball: ", perception.current_rotation_to_ball())
        if perception.current_rotation_to_ball() is not None:
            robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
        else:
            robot.behavior.turn_in_place(degrees(-45))
        time.sleep(0.1)  # Verzögerung Kamera-Feed ausgleichen
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
    if ((env.self.rotation < 80) & (env.self.rotation > -80)):
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
    ball_is_seen = env.ball.is_seen()
    distance_to_ball = 0.0
    unobstructed = robot.proximity.last_sensor_reading.unobstructed
    if not unobstructed:
        distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
        print("Distanz zu Ball: ", distance_to_ball)
    else: # falls infrarot-abstand nicht erkannt wurde
        # approximierte Distanz:
        difference_x = env.self.position_x - env.ball.position_x
        difference_y = env.self.position_y - env.ball.position_y
        distance_to_ball = ((difference_x**2 + difference_y**2)**0.5)

    while ball_is_seen and (unobstructed or (distance_to_ball > 110)):  # Vector soll bis 10 cm vor dem ball gerade auf ihn zufahren
        # abhaengig vom Abstand zum Ball fährt Vector bestimmte Distanz
        
        if ((distance_to_ball > 500) and ((x_goal_enemy - env.self.position_x)>300)): # Ball mehr als 50 cm entfernt
            print("ball weiter als 50cm entfernt", distance_to_ball)
            print((x_goal_enemy - env.self.position_x))
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            robot.behavior.drive_straight(distance_mm(350), speed_mmps(500))
        elif ((distance_to_ball > 400) and ((x_goal_enemy - env.self.position_x)>300)): # Ball mehr als 40 cm entfernt
            print("ball weiter als 40cm entfernt", distance_to_ball)
            print((x_goal_enemy - env.self.position_x))
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            robot.behavior.drive_straight(distance_mm(300), speed_mmps(500))
        elif ((distance_to_ball > 300) and ((x_goal_enemy - env.self.position_x)>300)): # Ball mehr als 30 cm entfernt
            print("ball weiter als 30cm entfernt", distance_to_ball)
            print((x_goal_enemy - env.self.position_x))
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            robot.behavior.drive_straight(distance_mm(200), speed_mmps(500))
        elif((distance_to_ball > 200) and ((x_goal_enemy - env.self.position_x)>200)):
            print("ball weiter als 20cm entfernt", distance_to_ball)
            print((x_goal_enemy - env.self.position_x))
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            robot.behavior.drive_straight(distance_mm(100), speed_mmps(500))
        elif((distance_to_ball > 150) and ((x_goal_enemy - env.self.position_x)>150)):
            print("ball weiter als 15cm entfernt", distance_to_ball)
            print((x_goal_enemy - env.self.position_x))
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            robot.behavior.drive_straight(distance_mm(75), speed_mmps(500))
        else:
            print("ball weniger als 15cm entfernt", distance_to_ball)
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            driving_distance = distance_to_ball - 50
            if driving_distance < 0:
                driving_distance = 0
            robot.behavior.drive_straight(distance_mm(distance_to_ball - 80), speed_mmps(500))
        unobstructed = robot.proximity.last_sensor_reading.unobstructed
    
        difference_x = env.self.position_x - env.ball.position_x
        difference_y = env.self.position_y - env.ball.position_y
        distance_to_ball = ((difference_x**2 + difference_y**2)**0.5)

        ball_is_seen = env.ball.is_seen()

    ball_is_seen = env.ball.is_seen()

    if ball_is_seen:
        print("Distanz zu Ball: ", distance_to_ball)
        print("Laufbahn berechenen")

        # Koordinaten vom Ball bestimmen
        time.sleep(0.2) # Verzögerung Kamera-Feed ausgleichen
        if perception.current_rotation_to_ball() is not None:
            robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
        
        distance_to_ball = distance_average(env, robot)
        unobstructed = robot.proximity.last_sensor_reading.unobstructed
        if not unobstructed: # wenn möglich nur infrarot
            distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
    
        x_vector = env.self.position_x
        y_vector = env.self.position_y
        print("x-postion vetor akutell : ", x_vector)
        print("y-postion vektor aktuell: ", y_vector)
        print("rotation: ", env.self.rotation)
        rotation_vector = env.self.rotation
        x_ball = x_vector + math.cos(math.radians(rotation_vector))*(distance_to_ball + 20)
        y_ball = y_vector + math.sin(math.radians(rotation_vector))*(distance_to_ball + 20)
        time.sleep(0.2)
        print("Infrarot Positon Ball: x = ", x_ball, "; y = ",  y_ball)
        # x_ball = env.ball.position_x
        # y_ball = env.ball.position_y
        #print("optisch position ball: x= ", x_ball, " y = ", y_ball)
        
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
            x_vector_pos2 = x_ball
            y_vector_pos2 = 0
            if y_ball > 600:
                y_vector_pos2 = y_ball + 100
            else:
                y_vector_pos2 = y_ball - 100
            # Vector fährt zu pos2
            turning_angel = turning_angel_vector(env, x_vector, y_vector_pos2)
            robot.behavior.turn_in_place(degrees(turning_angel))
            robot.behavior.drive_straight(distance_mm(abs(y_vector - y_vector_pos2)), speed_mmps(500))
            turning_angel = turning_angel_vector(env, x_vector_pos2, y_vector_pos2)
            robot.behavior.turn_in_place(degrees(turning_angel))
            robot.behavior.drive_straight(distance_mm(abs(x_vector - x_vector_pos2)), speed_mmps(500))
            turning_angel = turning_angel_vector(env, env.self.position_x, y_goal_enemy)
            robot.behavior.turn_in_place(degrees(turning_angel))

            # vector fährt mit ball vors tor
            robot.behavior.set_lift_height(0)
            time.sleep(0.3)
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            time.sleep(0.2)
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            robot.behavior.drive_straight(distance_mm(abs(env.self.position_y - y_goal_enemy-30)), speed_mmps(100))

            # vector fährt zu seiner schuss-position
            robot.behavior.drive_straight(distance_mm(-70), speed_mmps(500))
            # if env.self.position_y > y_goal_enemy:
            #     robot.behavior.turn_in_place(degrees(-45))
            # else:
            #     robot.behavior.turn_in_place(degrees(45))

            # robot.behavior.drive_straight(distance_mm(230), speed_mmps(500))
            # turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy)
            # robot.behavior.turn_in_place(degrees(turning_angel))
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            time.sleep(0.4) # Verzögerung Kamera-Feed ausgleichen
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            time.sleep(0.2)
            distance_to_ball = distance_average(env, robot)
            unobstructed = robot.proximity.last_sensor_reading.unobstructed
            if not unobstructed: # wenn möglich nur infrarot
                distance_to_ball = robot.proximity.last_sensor_reading.distance.distance_mm
        
            x_vector = env.self.position_x
            y_vector = env.self.position_y
            print("x-postion vetor akutell : ", x_vector)
            print("y-postion vektor aktuell: ", y_vector)
            rotation_vector = env.self.rotation
            x_ball = x_vector + math.cos(math.radians(rotation_vector))*(distance_to_ball + 20)
            y_ball = y_vector + math.sin(math.radians(rotation_vector))*(distance_to_ball + 20)

            # Berechnung des Richtungsvektors
            x_direction = 1
            y_direction = (y_goal_enemy - y_ball)/(x_goal_enemy - x_ball)

            # Normieren des Richtungsvektors
            abs_value = ((x_direction**2)+(y_direction**2))**0.5  # Betrag des Vectors
            x_direction_norm = (1/abs_value)*x_direction
            y_direction_norm = (1/abs_value)*y_direction

            # Berechnen der Koordinaten des Punktes [2] 7 cm hinter dem Ball, in
            # Verlängerung zur Schussbahn, zu dem Vector fahren soll.
            x_vector_pos2 = -70 * x_direction_norm + x_ball
            y_vector_pos2 = -70 * y_direction_norm + y_ball
            print("Neu brechnete Position Vector: x = ", x_vector_pos2, " y = ",y_vector_pos2)
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

            turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) # Berechenen des Winkels um den sich Vector drehen muss (Position 2)
            print("Turning-Angle zum Tor: ", turning_angel)
            robot.behavior.turn_in_place(degrees(turning_angel))  # Vector dreht sich auf Position 2

            time.sleep(0.1)
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            time.sleep(0.2)
            if perception.current_rotation_to_ball() is not None:
                robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            distance_to_enemy_goal = ((env.self.position_x - x_goal_enemy)**2+(env.self.position_y - y_goal_enemy)**2)**0.5 # Abstand zu gegnerischem Tor

            if distance_to_enemy_goal > 500:
                # falls vector weiter als 50cm vom gegnerischen Tor entfernt ist,
                # soll er denn ball bis 30cm vor das tor führen und dann schiessen
                robot.behavior.set_lift_height(0)
                robot.behavior.drive_straight(distance_mm(distance_to_enemy_goal-300), speed_mmps(100))
            shooting(env, robot)

        else: # Ball nicht im toten Winkel
            # Berechnung des Richtungsvektors
            x_direction = 1
            y_direction = (y_goal_enemy - y_ball)/(x_goal_enemy - x_ball)

            # Normieren des Richtungsvektors
            abs_value = ((x_direction**2)+(y_direction**2))**0.5  # Betrag des Vectors
            x_direction_norm = (1/abs_value)*x_direction
            y_direction_norm = (1/abs_value)*y_direction

            # Berechnen der Koordinaten des Punktes [2] 7 cm hinter dem Ball, in
            # Verlängerung zur Schussbahn, zu dem Vector fahren soll.
            x_vector_pos2 = -70 * x_direction_norm + x_ball
            y_vector_pos2 = -70 * y_direction_norm + y_ball
            print("Neu brechnete Position Vector: x = ", x_vector_pos2, " y = ",y_vector_pos2)
            y_diffrence_pos_1_2 = abs(y_vector - y_vector_pos2)
            if (y_vector_pos2 > (env._FIELD_LENGTH_Y-3) or y_vector_pos2 < 3):
                # falls berechnete Position 2 des Vectors für ihn nicht erreichbar ist
                # (ausserhalb des Spielfelds) schiesst er den Ball über Bande und
                # dreht sich danach Richtung Tor
                shooting(env, robot)  # Vector fährt zum Ball und schiesst
                turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) # Berechenen des Winkels um den sich Vector drehen muss
                print("Turning-Angle zum Tor: ", turning_angel)
                robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich zum Tor

            elif y_diffrence_pos_1_2 < 20:
                # falls unterschied zur neuen position nicht zu groß ist, soll vector einfach schiessen
                shooting(env, robot)  # Vector fährt zum Ball und schießt

            else:   
                # ansonsten fährt er zur berechneten Position 2 und schiesst
                # Vector fährt von Positon 1 (aktuell) zur Position 2
                '''eventuell mit go_to_pose(pose)'''
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

                turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) # Berechenen des Winkels um den sich Vector drehen muss (Position 2)
                print("Turning-Angle zum Tor: ", turning_angel)
                robot.behavior.turn_in_place(degrees(turning_angel))  # Vector dreht sich auf Position 2

                # pose = Pose(x=(x_vector_pos2 - env._POSITION_START_X), y=(y_vector_pos2 - env._POSITION_START_Y), z=0, angle_z=degrees(0))
                # robot.behavior.go_to_pose(pose)

                # turning_angel = turning_angel_vector(env, x_goal_enemy, y_goal_enemy) # Berechenen des Winkels um den sich Vector drehen muss (Position 2)
                # print("Turning-Angle zum Tor: ", turning_angel)
                # robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich auf Position 1
                
                time.sleep(0.1)
                if perception.current_rotation_to_ball() is not None:
                    robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
                time.sleep(0.2)
                if perception.current_rotation_to_ball() is not None:
                    robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
                time.sleep(0.2)
                if perception.current_rotation_to_ball() is not None:
                    robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
                distance_to_enemy_goal = ((env.self.position_x - x_goal_enemy)**2+(env.self.position_y - y_goal_enemy)**2)**0.5 # Abstand zu gegnerischem Tor

                if distance_to_enemy_goal > 500:
                    # falls vector weiter als 50cm vom gegnerischen Tor entfernt ist,
                    # soll er denn ball bis 30cm vor das tor führen und dann schiessen
                    robot.behavior.set_lift_height(0)
                    robot.behavior.drive_straight(distance_mm(distance_to_enemy_goal-300), speed_mmps(100))
                
                shooting(env, robot)  # Vector fährt zum Ball und schießt

                # vector fährt ball hinter her
                if perception.current_rotation_to_ball() is not None:
                    robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
                    time.sleep(0.1)
                if (x_goal_enemy - env.self.position_x) > 500:
                    robot.behavior.drive_straight(distance_mm(200), speed_mmps(500))
                    print("drive 200")
                elif (x_goal_enemy - env.self.position_x) > 400:
                    robot.behavior.drive_straight(distance_mm(100), speed_mmps(500))
                    print("drive 100")
                ball_is_seen = env.ball.is_seen()
                if ball_is_seen:
                    play_offensive(env, robot)
                else:
                    robot.behavior.turn_in_place(degrees(-45))
                # danach wird wieder look_for_ball()aufgerufen


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
    ball_is_seen = env.ball.is_seen()
    rotation_to_ball = perception.current_rotation_to_ball()
    ball_in_line = ball_is_seen and rotation_to_ball is not None

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
                    turning_angel = turning_angel -45
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
    turning_angel = turning_angel_vector(env, 500, 500) # Berechnen des Winkel um den sich Vector zur letzten bekannten Positon des Balls drehen muss 
    print("Turning-Angle zum Ball: ", turning_angel)
    robot.behavior.turn_in_place(degrees(turning_angel)) # Vector dreht sich zur letzten bekannten Postion des Balls
    

    # Verteidigung im Tor:
    # Vector sucht in einem 180° Winkel vor ihm
    # findet er ihn nicht, fährt er 20cm vor und sucht analog (insgesamt 3x)
    # hat er ihn gefunden, wird play_offensive() aufgerufen
    # andernfalls wird look_for_ball() aufgerufen
    print("sleep")
    time.sleep(1) # verzögerung kamera-feed ausgleichen
    ball_is_seen = env.ball.is_seen()
    if not ball_is_seen:
        robot.behavior.turn_in_place(degrees(-45))
        time.sleep(0.1) # Verzögerung Kamera-Feed ausgleichen
        ball_is_seen = env.ball.is_seen()
    i = 0
    while not ball_is_seen and (i < 3):
        
        robot.behavior.turn_in_place(degrees(90))
        time.sleep(0.1) # Verzögerung Kamera-Feed ausgleichen
        ball_is_seen = env.ball.is_seen()
        if not ball_is_seen:
            robot.behavior.turn_in_place(degrees(-45))
            time.sleep(0.1) # Verzögerung Kamera-Feed ausgleichen
            if not ball_is_seen:
                robot.behavior.drive_straight(distance_mm(200), speed_mmps(500))
                ball_is_seen = env.ball.is_seen()
                if not ball_is_seen:
                    robot.behavior.turn_in_place(degrees(-45))
                    time.sleep(0.1) # Verzögerung Kamera-Feed ausgleichen
                    ball_is_seen = env.ball.is_seen()
        i = i + 1
    if ball_is_seen:
        play_offensive(env, robot)
    else:
        look_for_ball(env, robot)


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
    unobstructed = True
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
        difference_x = env.self.position_x - env.ball.position_x
        difference_y = env.self.position_y - env.ball.position_y
        distance_to_ball_approx = ((difference_x**2 + difference_y**2)**0.5)
        print("Distanz zu Ball approximiert: ", distance_to_ball_approx)
        return distance_to_ball_approx


def shooting(env, robot):
    ''' Vector fährt auf Ball zu, korregiert eventuell Fahrtrichtung.
    Ist er nah genug am Ball, soll er mit Hilfe seines Lifts schießen.
    '''
    print("shooting()")
    
    robot.behavior.set_lift_height(1)
    if perception.current_rotation_to_ball() is not None:
        robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
        time.sleep(0.1) # Verzögerung Kamera-Feed ausgleichen

    distance_to_ball = distance_average(env, robot)
    
    if distance_to_ball is not -1:
        # Vector soll in Schussdistanz zum Ball fahren
        if distance_to_ball > 80:
            robot.behavior.drive_straight(distance_mm(distance_to_ball-8), speed_mmps(500))
        elif distance_to_ball > 50:
            robot.behavior.drive_straight(distance_mm(distance_to_ball-18), speed_mmps(500))
        else:
            robot.behavior.drive_straight(distance_mm(distance_to_ball-30), speed_mmps(500))
        robot.behavior.set_lift_height(0.0, accel=1000.0, max_speed=1000.0, duration=0.0)
        print("shot")
        
        time.sleep(0.2) # Ball wegrollen lassen

        if perception.current_rotation_to_ball() is not None:
            robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
        
        distance_to_ball = distance_average(env, robot)
        ball_is_seen = env.ball.is_seen()
        while (distance_to_ball < 100 and distance_to_ball >= 0 and ball_is_seen):  # falls der Ball nicht richtig geschossen wurde, wird es nochmal versucht
            if distance_to_ball is not -1:
                robot.behavior.set_lift_height(1.0, accel=1000.0, max_speed=1000.0, duration=0.0)
                robot.behavior.drive_straight(distance_mm(distance_to_ball-18), speed_mmps(500))
                robot.behavior.set_lift_height(0.0, accel=1000.0, max_speed=1000.0, duration=0.0)
                print("shot")
            
                time.sleep(0.2) # Ball wegrollen lassen

                if perception.current_rotation_to_ball() is not None:
                    robot.behavior.turn_in_place(degrees(perception.current_rotation_to_ball())) # vector dreht sich zum Ball
            
                distance_to_ball = distance_average(env, robot)
            ball_is_seen = env.ball.is_seen()
        print("vorbei")
    


   
