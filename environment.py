import anki_vector
import multiprocessing
import time
from anki_vector.util import degrees, Pose, Speed, Distance
from anki_vector import behavior
import pygame
import random
from pygame.locals import *
import threading

NAME = 'Vector-N8G2'
IP = '192.168.0.189'
SERIAL = '008014c1'


class Environment():
    '''Representation of vectors environment/ the soccer field
    with all its objects and functions to return those objects.
    '''

    def __init__(self, robot, field_length_x, field_length_y,
                 goal_width, ball_diameter, position_start_x, position_start_y,
                 enable_environment_viewer):
        self._robot = robot
        self._ROBOT_SIZE_X = 100
        self._ROBOT_SIZE_Y = 60
        self._GOAL_WIDTH = goal_width
        self._BALL_DIAMETER = ball_diameter
        self._FIELD_LENGTH_X = field_length_x
        self._FIELD_LENGTH_Y = field_length_y
        self._POSITION_START_X = position_start_x
        self._POSITION_START_Y = position_start_y
        self._self = EnvironmentObject('Self',
                                       self._ROBOT_SIZE_X,
                                       self._ROBOT_SIZE_Y,
                                       self._POSITION_START_X,
                                       self._POSITION_START_Y,
                                       0.0, 0, self)
        self._ball = EnvironmentObject('Ball',
                                       self._BALL_DIAMETER,
                                       self._BALL_DIAMETER,
                                       (self._FIELD_LENGTH_X)/2,
                                       self._POSITION_START_Y,
                                       0.0, 0, self)
        self._enemy = EnvironmentObject('Enemy',
                                        self._ROBOT_SIZE_X,
                                        self._ROBOT_SIZE_Y,
                                        self._FIELD_LENGTH_X-self._POSITION_START_X,
                                        self._POSITION_START_Y,
                                        180.0, 0, self)
        self._goal_self = EnvironmentObject('Goal_self',
                                            0,
                                            self._GOAL_WIDTH,
                                            0,
                                            self._POSITION_START_Y,
                                            0.0, 0, self)
        self._goal_enemy = EnvironmentObject('Goal_enemy',
                                             0,
                                             self._GOAL_WIDTH,
                                             self._FIELD_LENGTH_X,
                                             self._POSITION_START_Y,
                                             0.0, 0, self)
        if enable_environment_viewer is True:
            self.environment_viewer = EnvironmentViewer(self)
            environment_viewer_thread = threading.Thread(environment_viewer.show())
            environment_viewer_thread.start()
        print('Environment initialized with objects in startposition')

    def environment_objects(self):
        '''Returns a list of all the objects on the map in the following order:
        Self, ball, enemy, goal_enemy, goal_self as EnvironmentObjects
        '''
        return [self.self, self._ball, self._enemy,
                self._goal_enemy, self._goal_self]

    @property
    def self(self):
        if self._robot is None:
            return self._self
        else:
            position_x = self._robot.pose.to_matrix().pos_xyz[0]
            position_y = self._robot.pose.to_matrix().pos_xyz[1]
            rotation = self._robot.pose_angle_rad
            self._self.position_x = position_x - self._POSITION_START_X
            self._self.position_y = position_y - self._POSITION_START_Y
            self._self.rotation = rotation
            self._self.last_seen = time.time()
            print(f'Updated {self._self.tag} position.')
            return self._self

    @property
    def ball(self):
        return self._ball

    @property
    def enemy(self):
        return self._enemy

    @property
    def goal_self(self):
        return self._goal_self

    @property
    def goal_enemy(self):
        return self._goal_enemy

    @property
    def robot(self):
        return self._robot

    @property
    def field_length_x(self):
        return self._FIELD_LENGTH_X

    @property
    def field_length_y(self):
        return self._FIELD_LENGTH_Y


class EnvironmentObject():

    def __init__(self, tag, size_x, size_y, position_x, position_y,
                 rotation, last_seen, environment):
        self._tag = tag
        self._size_x = size_x
        self._size_y = size_y
        self._position_x = position_x  # - environment._POSITION_START_X
        self._position_y = position_y  # - environment._POSITION_START_Y
        self._rotation = rotation  # in Grad
        self._last_seen = last_seen  # In Sekunden nach 01.01.1970
        self._environment = environment

    def pose(self):
        if self._tag == 'Self':
            self.position_x = self._environment.robot.pose.to_matrix().pos_xyz[0] - self._environment._POSITION_START_X
            self.position_y = self._environment.robot.pose.to_matrix().pos_xyz[1] - self._environment._POSITION_START_Y
            self.rotation = self._environment.robot.pose_angle_rad
            print(f'Updated {self._tag} position.')
            return Pose(x=self.position_x,
                        y=self.position_y,
                        z=0,
                        angle_z=anki_vector.util.Angle(degrees=self._rotation))
        else:
            return Pose(x=self.position_x,
                        y=self.position_y,
                        z=0,
                        angle_z=anki_vector.util.Angle(degrees=0))

    def _was_seen_recently(self):
        time_threshold_recently = 0.5  # in Sekunden
        if (self._last_seen+time_threshold_recently) - time.time() >= 0:
            return True
        else:
            return False

    def is_seen(self):
        return self._was_seen_recently()

    @property
    def tag(self):
        return self._tag

    @property
    def size_x(self):
        return self._size_x

    @property
    def size_y(self):
        return self._size_y

    @property
    def position_x(self):
        return self._position_x

    @position_x.setter
    def position_x(self, position_x):
        self._position_x = position_x - self._environment._POSITION_START_X

    @property
    def position_y(self):
        return self._position_y

    @position_y.setter
    def position_y(self, position_y):
        self._position_y = position_y - self._environment._POSITION_START_Y

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation

    @property
    def last_seen(self):
        return self._last_seen

    @last_seen.setter
    def last_seen(self, last_seen):
        self._last_seen = last_seen

    @property
    def environment(self):
        return self._environment


class EnvironmentViewer:

    def __init__(self, environment):
        self._environment = environment

    def scale(self, value):
        # TODO Automatisch als Prozent des Displays skalieren
        return int(value/3)
    
    def draw_field(self, window,
                   window_height,
                   window_width,
                   edge,
                   line_thickness,
                   goal_size_y,
                   color_background,
                   color_line,
                   color_goal):

        goal_area_width = self.scale(300)
        goal_area_height = self.scale(150)
        penalty_area_width = self.scale(600)
        penalty_area_height = self.scale(300)
        print('Feld wird geladen...')
        # background
        window.fill(color_background)
        # field
        pygame.draw.rect(window, color_background, Rect(edge, edge, window_width - 2 * edge, window_height - 2 * edge))
        # goal self
        pygame.draw.rect(window, color_goal, Rect(window_width/2 - goal_size_y/2,
                                                0,
                                                goal_size_y,
                                                edge))
        # goal enemy
        pygame.draw.rect(window, color_goal, Rect(window_width/2 - goal_size_y/2,
                                                window_height-edge,
                                                goal_size_y,
                                                edge))
        # center circle
        pygame.draw.circle(window, color_line, (window_width/2, window_height/2), window_width/6, line_thickness)
        # touchline
        pygame.draw.lines(window, color_line, True, [(edge, edge), 
                                                        (edge, window_height-edge),
                                                        (window_width-edge, window_height-edge),
                                                        (window_width-edge, edge)], line_thickness)
        # center line
        pygame.draw.line(window, color_line, (edge, window_height/2), (window_width-edge, window_height/2), line_thickness)
        # goal area self
        pygame.draw.lines(window, color_line, False, [(window_width/2 - goal_area_width/2, edge),
                                                        (window_width/2-goal_area_width/2, edge + goal_area_height),
                                                        (window_width/2+goal_area_width/2, edge + goal_area_height),
                                                        (window_width/2+goal_area_width/2, edge)], line_thickness)
        # goal area enemy
        pygame.draw.lines(window, color_line, False, [(window_width/2-goal_area_width/2, window_height-edge),
                                                        (window_width/2-goal_area_width/2, window_height - edge - goal_area_height),
                                                        (window_width/2+goal_area_width/2, window_height - edge - goal_area_height),
                                                        (window_width/2+goal_area_width/2, window_height - edge)], line_thickness)       
        # penalty area self
        pygame.draw.lines(window, color_line, False, [(window_width/2-penalty_area_width/2, edge),
                                                        (window_width/2-penalty_area_width/2, edge + penalty_area_height),
                                                        (window_width/2+penalty_area_width/2, edge + penalty_area_height),
                                                        (window_width/2+penalty_area_width/2, edge)], line_thickness)
        # penalty area enemy
        pygame.draw.lines(window, color_line, False, [(window_width/2-penalty_area_width/2, window_height-edge),
                                                        (window_width/2-penalty_area_width/2, window_height - edge - penalty_area_height),
                                                        (window_width/2+penalty_area_width/2, window_height - edge - penalty_area_height),
                                                        (window_width/2+penalty_area_width/2, window_height - edge)], line_thickness)
        print('Feld geladen.')


    def show(self):

        GREY_DARK = (30, 30, 30)
        GREY_LIGHT = (50,50,50)
        BLACK = (0, 0, 0)
        WHITE = (155, 155, 155)
        ORANGE = (209, 134, 0)

        frames_per_second = 25
        edge = 10
        line_thickness = 2
        window_width = self.scale(self._environment.field_length_y) + 2*edge
        window_height = self.scale(self._environment.field_length_x) + 2*edge
        robot_size_x = self.scale(self._environment.self.size_x)
        robot_size_y = self.scale(self._environment.self.size_y)
        ball_size_x = self.scale(self._environment.ball.size_x)
        goal_size_y = self.scale(self._environment.goal_self.size_y)

        print('Viewer wird initialisiert...')
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption("VectorEnvironmentViewer")
        window = pygame.display.set_mode((window_width, window_height))
        clock = pygame.time.Clock()

        self_png = pygame.image.load("vector_without_background.png").convert_alpha()
        self_png = pygame.transform.scale(self_png, (int(1.4*robot_size_x), int(1.4*robot_size_y)))
        enemy_png = pygame.image.load("vector_without_background.png").convert_alpha()
        enemy_png = pygame.transform.scale(enemy_png, (int(1.4*robot_size_x), int(1.4*robot_size_y)))        
        
        self.draw_field(window, window_height, window_width,
                        edge, line_thickness, goal_size_y, 
                        GREY_DARK, GREY_LIGHT, BLACK)

        quit = False
        help = False

        while not quit:

            for event in pygame.event.get():
                # print(event)
                if event.type == QUIT:
                    quit = True
            
            self_position_x = self.scale(self._environment.self.position_x)
            self_position_y = self.scale(self._environment.self.position_y)
            self_rotation = self._environment.self.rotation
            enemy_position_x = self.scale(self._environment.enemy.position_y)
            enemy_position_y = self.scale(self._environment.enemy.position_x)
            enemy_rotation = self._environment.enemy.rotation
            ball_position_x = self.scale(self._environment.ball.position_x)
            ball_position_y = self.scale(self._environment.ball.position_y)

            vector = Rect(self_position_y-robot_size_y/2 + edge,
                          self_position_x-robot_size_x*0.8 + edge,
                          robot_size_y,
                          robot_size_x)
            enemy = Rect(enemy_position_y-robot_size_y/2 + edge,
                         enemy_position_x-robot_size_x*0.2 + edge,
                         robot_size_y,
                         robot_size_x)

            #Draw Ball
            pygame.draw.circle(window,
                               ORANGE,
                               (ball_position_y + edge,
                                ball_position_x + edge),
                               ball_size_x/2)
            pygame.draw.rect(window, WHITE, vector)
            pygame.draw.rect(window, WHITE, enemy)
            # pygame.draw.polygon(window, ORANGE, [(window_width/2, window_height/2-10), (window_width/2, window_height/2+10), (window_width/2-20, window_height/2)])
            
            #Draw Self
            self_png = pygame.transform.rotate(self_png, 90.0 + self_rotation)
            window.blit(self_png, (self_position_y - robot_size_y/2 + edge,
                                   self_position_x - robot_size_x*0.8 + edge))
            #Draw Enemy
            enemy_png = pygame.transform.rotate(enemy_png, 90.0 + enemy_rotation)
            window.blit(enemy_png, (enemy_position_y - robot_size_y/2 + edge,
                                    enemy_position_x - robot_size_x*0.2 + edge))


            if help is not True:
                print(f'Painted Vector at {self._environment.self.position_x},{self_position_y}')
                print(f'Painted Enemy at {self._environment.enemy.position_x},{self._environment.enemy.position_y}')
                print(f'Painted Ball at {self._environment.ball.position_x},{self._environment.ball.position_y}')
                help = True

            pygame.display.update()
            clock.tick(frames_per_second)                    

        pygame.quit()


class EnvironmentTest():

    def test_viewer(self, environment):
        print('+++ViewerTest+++')
        environment_viewer = EnvironmentViewer(environment)
        environment_viewer_thread = threading.Thread(environment_viewer.show())
        environment_viewer_thread.start()

    def test_custom_object(self, robot, environment):
        print('+++CustomObject-Test+++')
        # Erstellt die Wände
        wall_left = robot.world.create_custom_fixed_object(
            Pose(x=-environment._POSITION_START_X, y=environment._POSITION_START_Y, z=0, angle_z=degrees(0)), 
            x_size_mm=environment.field_length, 
            y_size_mm=environment.wall_thickness, 
            z_size_mm=environment.field_window_height,
            relative_to_robot=True)
        wall_right = robot.world.create_custom_fixed_object(
            Pose(x=-environment._POSITION_START_X, y=-environment._POSITION_START_Y, z=0, angle_z=degrees(0)), 
            x_size_mm=environment.field_length, 
            y_size_mm=environment.wall_thickness, 
            z_size_mm=environment.field_window_height,
            relative_to_robot=True)
        wall_self = robot.world.create_custom_fixed_object(
            Pose(x=-environment._POSITION_START_X, y=-environment._POSITION_START_Y, z=0, angle_z=degrees(90)), 
            x_size_mm=environment.field_window_width, 
            y_size_mm=environment.wall_thickness, 
            z_size_mm=environment.field_window_height,
            relative_to_robot=True)
        wall_oponent = robot.world.create_custom_fixed_object(
            Pose(x=-environment._POSITION_START_X, y=environment.field_length-environment._POSITION_START_Y, z=0, angle_z=degrees(90)), 
            x_size_mm=environment.field_window_width, 
            y_size_mm=environment.wall_thickness, 
            z_size_mm=environment.field_window_height,
            relative_to_robot=True)  
        print("Alle Objekte:")
        for obj in robot.world.all_objects:
            print(obj)  

    def test_proximity(self, robot, environment):
        print('+++Proximity-Test:+++')
        for i in range(1, 20):
            iteration_done = False
            # robot.behavior.drive_straight(Distance(distance_mm=100.0), speed=Speed(speed_mmps=100.0))
            proximity_data = robot.proximity.last_sensor_reading
            while robot.accel != 0 and iteration_done is False:
                if proximity_data is not None:
                    print(f'Distanz: {proximity_data.distance}'
                          f', Objekt gefunden: {proximity_data.found_object}'
                          f', Lift im Weg: {proximity_data.is_lift_in_fov}'
                          f', Signalqualität: {proximity_data.signal_quality}'
                          f', Unobstructed: {proximity_data.unobstructed}'
                          '.')
                # robot.behavior.drive_straight(Distance(distance_mm=100.0), speed=Speed(speed_mmps=100.0))
                time.sleep(2)
                iteration_done = True

    def test_general(self, robot, environment):
        print("Grundtest gestartet")
        test_done = False
        print("Fahre zum Startpunkt...")
        robot.behavior.go_to_pose(environment.self.pose(), False, 3)
        while robot.accel != 0 and test_done is False:
            print(f"Beim Startpunkt ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
            print("Fahre zum _Ball...")
            robot.behavior.go_to_pose(environment._ball.pose(), False, 3)
            while robot.accel != 0 and test_done is False:
                print(f"Beim _Ball ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
                print("Fahre zum Gegner...")
                robot.behavior.go_to_pose(environment._enemy.pose(), False, 3)
                while robot.accel != 0 and test_done is False:
                    print(f"Beim Gegner ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
                    print("Fahre zum eigenen Tor...")
                    robot.behavior.go_to_pose(environment._goal_self.pose(), False, 3)
                    while robot.accel != 0 and test_done is False:
                        print(f"Beim eigenen Tor ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
                        print("Fahre zum gegenerischen Tor...")
                        robot.behavior.go_to_pose(environment.goal__enemy.pose(), False, 3)
                        while robot.accel != 0 and test_done is False:
                            print(f"Beim gegnerischen Tor ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
                            test_done = True

    def test_winkelformat(self, robot, environment):
        print('+++Winkelformatvergleich+++')
        print(f'Angle(): {anki_vector.util.Angle(degrees=0)}')
        print(f'degrees(): {degrees(environment._enemy.rotation)}')
        print(f'Angle(rotation): {anki_vector.util.Angle(degrees=environment.self.rotation)}')

    def test(self):
        anki_vector_available = False
        if anki_vector_available is True:
            robot = anki_vector.Robot(serial=SERIAL)
            environment = Environment(robot,
                                      field_length_x=2000.0,
                                      field_length_y=1000.0,
                                      goal_width=200.0,
                                      ball_diameter=40.0,
                                      position_start_x=100.0,
                                      position_start_y=500.0,
                                      enable_environment_viewer=False)
            robot.connect()
            robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange

            with behavior.ReserveBehaviorControl(serial=SERIAL):

                # self.test_general(robot, environment)
                # self.test_winkelformat(robot, environment)
                self.test_proximity(robot, environment)
                # self.test_custom_object(robot, environment)

            robot.disconnect()

        else:
            robot = None
            environment = Environment(robot,
                                      field_length_x=2000.0,
                                      field_length_y=1000.0,
                                      goal_width=200.0,
                                      ball_diameter=40.0,
                                      position_start_x=100.0,
                                      position_start_y=500.0,
                                      enable_environment_viewer=False)
            self.test_viewer(environment)


if __name__ == '__main__':
    environment_test = EnvironmentTest()
    environment_test.test()
