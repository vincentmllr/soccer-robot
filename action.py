
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
    y_direction = (500 - y_ball)/(2000 - x_ball)

    # Normieren des Richtungsvektors
    abs_value = ((x_direction**2)+(y_direction**2))**0.5  # Betrag
    x_direction_norm = (1/abs_value)*x_direction
    y_direction_norm = (1/abs_value)*y_direction

    # Berechnen der Koordinaten des Punktes 10cm hinter dem Ball, in
    # Verlängerung zur Schussbahn, zu dem Vector fahren soll.
    x_vector_new = -100 * x_direction_norm + x_ball
    y_vector_new = -100 * y_direction_norm + x_ball
    print("Neu brechnete Position Vector: x = " + x_vector_new + " y = "+y_vector_new)

    # Vector fährt zur Position


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
