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
                                       degrees(0), 0, self)
        self._ball = EnvironmentObject('Ball',
                                       self._BALL_DIAMETER,
                                       self._BALL_DIAMETER,
                                       (self._FIELD_LENGTH_Y)/2,
                                       self._POSITION_START_Y,
                                       degrees(0), 0, self)
        self._enemy = EnvironmentObject('Enemy',
                                        self._ROBOT_SIZE_X,
                                        self._ROBOT_SIZE_Y,
                                        self._FIELD_LENGTH_X-self._POSITION_START_X,
                                        self._POSITION_START_Y,
                                        degrees(0), 0, self)
        self._goal_self = EnvironmentObject('Goal_self',
                                            0,
                                            self._GOAL_WIDTH,
                                            0,
                                            self._POSITION_START_Y,
                                            degrees(0), 0, self)
        self._goal_enemy = EnvironmentObject('Goal_enemy',
                                             0,
                                             self._GOAL_WIDTH,
                                             self._FIELD_LENGTH_X,
                                             self._POSITION_START_Y,
                                             degrees(0), 0, self)
        if enable_environment_viewer is True:
            self.environment_viewer = EnvironmentViewer(self)
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
            position_x = self._robot.pose.to_matrix.pos_xyz[0]
            position_y = self._robot.pose.to_matrix.pos_xyz[1]
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
            self.position_x = self._environment.robot.pose.to_matrix.pos_xyz[0] - self._environment._POSITION_START_X
            self.position_y = self._environment.robot.pose.to_matrix.pos_xyz[1] - self._environment._POSITION_START_Y
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
        return self._rotation()

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
        return int(value/3)

    def show(self):

        GREY = (30, 30, 30)
        BLACK = (0, 0, 0)
        WHITE = (155, 155, 155)
        frames_per_second = 25
        window_width = self.scale(self._environment.field_length_y)
        window_height = self.scale(self._environment.field_length_x)

        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption("VectorEnvironmentViewer")
        window = pygame.display.set_mode((window_width, window_height))
        clock = pygame.time.Clock()

        quit = False
        help = False

        while not quit:
            window.fill(GREY)
            # TODO Feld designen mit draw.Rect()
            keyspressed = pygame.key.get_pressed()
            for event in pygame.event.get():
                print(event)
                if event.type == QUIT:
                    quit = True
            if keyspressed[ord("a")]:
                quit = True

            vector = Rect(self.scale(self._environment.self.position_y-self._environment.self.size_y/2),
                          self.scale(self._environment.self.position_x-self._environment.self.size_x*0.8),
                          self.scale(self._environment.self.size_y),
                          self.scale(self._environment.self.size_x))
            enemy = Rect(self.scale(self._environment.enemy.position_y-self._environment.enemy.size_y/2),
                         self.scale(self._environment.enemy.position_x-self._environment.enemy.size_x*0.2),
                         self.scale(self._environment.enemy.size_y),
                         self.scale(self._environment.enemy.size_x))
            pygame.draw.rect(window, WHITE, vector)
            pygame.draw.rect(window, BLACK, enemy )

            if help is not True:
                print(f'Painted Vector at {self._environment.self.position_x},{self._environment.self.position_y}')
                print(f'Painted Enemy at {self._environment.enemy.position_x},{self._environment.enemy.position_y}')
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
