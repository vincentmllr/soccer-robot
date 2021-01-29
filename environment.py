import anki_vector
import time
from anki_vector.connection import ControlPriorityLevel
from anki_vector.util import degrees, Pose
from anki_vector import behavior
import pygame
from pygame.constants import K_0
from pygame.locals import Rect, QUIT
import threading
import math
import tkinter
from tkinter import *

NAME = 'Vector-N8G2'
NAME_VINCENT = 'Vector-R7U1'
IP_VINCENT = '192.168.68.159'
SERIAL = '008014c1'
SERIAL_VINCENT = '00804ea0'


class Environment():
    '''Representation of vectors environment/ the soccer field
    with all its objects and functions to return those objects.
    '''

    def __init__(self, robot, field_length_x, field_length_y,
                 goal_width, ball_diameter, position_start_x, position_start_y):
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
                                       0.0, 0, self, 180.0)
        self._ball = EnvironmentObject('Ball',
                                       self._BALL_DIAMETER,
                                       self._BALL_DIAMETER,
                                       (self._FIELD_LENGTH_X)/2,
                                       self._POSITION_START_Y,
                                       0.0, 0, self)
        self._enemy = EnvironmentObject('Enemy',
                                        self._ROBOT_SIZE_X,
                                        self._ROBOT_SIZE_Y,
                                        self._FIELD_LENGTH_X
                                        - self._POSITION_START_X,
                                        self._POSITION_START_Y,
                                        180.0, 0, self, 0.0, 180.0)
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
        self._viewer = EnvironmentViewer(self)
        self._environment_viewer = threading.Thread(target=self._viewer.show)
        # Alternativ: Das in Main funktioniert auf jeden Fall
        # viewer_thread = threading.Thread(target=env.environment_viewer.show)
        # viewer_thread.start()

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
            rotation = self._robot.pose_angle_rad / math.pi * 180.0 
            self._self.position_x = position_x + self._POSITION_START_X
            self._self.position_y = position_y + self._POSITION_START_Y
            self._self.rotation = rotation
            self._self.last_seen = time.time()
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

    @property
    def environment_viewer(self):
        return self._environment_viewer


class EnvironmentObject():

    def __init__(self, tag, size_x, size_y, position_x, position_y,
                 rotation, last_seen, environment, angle_to_goal_self=0.0,
                 angle_to_goal_enemy=0.0, angle_to_ball=0.0):
        self._tag = tag
        self._size_x = size_x
        self._size_y = size_y
        self._position_x = position_x
        self._position_y = position_y
        self._rotation = rotation  # in Grad
        self._last_seen = last_seen  # In Sekunden nach 01.01.1970
        self._environment = environment
        self._angle_to_goal_self = angle_to_goal_self
        self._angle_to_goal_enemy = angle_to_goal_enemy
        self._angle_to_ball = angle_to_ball

    def pose(self):
        if self._tag == 'Self':
            position_x = self._robot.pose.to_matrix().pos_xyz[0]
            position_y = self._robot.pose.to_matrix().pos_xyz[1]
            rotation = self._robot.pose_angle_rad / math.pi * 180.0
            self._self.position_x = position_x + self._POSITION_START_X
            self._self.position_y = position_y + self._POSITION_START_Y
            self._self.rotation = rotation
            self._self.last_seen = time.time()
            # print(f'Updated {self._tag} position.')
            return Pose(x=self.position_x, # TODO Korrigieren
                        y=self.position_y,
                        z=0,
                        angle_z=anki_vector.util.Angle(degrees=self._rotation))
        else:
            return Pose(x=self.position_x,
                        y=self.position_y,
                        z=0,
                        angle_z=anki_vector.util.Angle(degrees=0))

    def _was_seen_recently(self, now):
        time_threshold_recently = 0.5  # in Sekunden
        if (self._last_seen + time_threshold_recently) - now >= 0:
            return True
        else:
            return False

    def is_seen(self):
        now = time.time()
        return self._was_seen_recently(now)

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
        self._position_x = position_x

    @property
    def position_y(self):
        return self._position_y

    @position_y.setter
    def position_y(self, position_y):
        self._position_y = position_y

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

    @property
    def angle_to_goal_self(self):
        return self._angle_to_goal_self

    @angle_to_goal_self.setter
    def angle_to_goal_self(self, angle_to_goal_self):
        self._angle_to_goal_self = angle_to_goal_self

    @property
    def angle_to_goal_enemy(self):
        return self._angle_to_goal_enemy

    @angle_to_goal_enemy.setter
    def angle_to_goal_enemy(self, angle_to_goal_enemy):
        self._angle_to_goal_enemy = angle_to_goal_enemy

    @property
    def angle_to_ball(self):
        return self._angle_to_ball

    @angle_to_ball.setter
    def angle_to_ball(self, angle_to_ball):
        self._angle_to_ball = angle_to_ball 


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
        # background
        window.fill(color_background)
        # field
        rect_field = Rect(edge,
                          edge,
                          window_width - 2*edge,
                          window_height - 2*edge)
        pygame.draw.rect(window, color_background, rect_field)
        # goal self
        rect_goal_self = Rect(window_width/2 - goal_size_y/2,
                              0,
                              goal_size_y,
                              edge)
        pygame.draw.rect(window, color_goal, rect_goal_self)
        # goal enemy
        rect_goal_enemy = Rect(window_width/2 - goal_size_y/2,
                               window_height-edge,
                               goal_size_y,
                               edge)
        pygame.draw.rect(window, color_goal, rect_goal_enemy)
        # center circle
        pygame.draw.circle(window, color_line,
                           (window_width/2, window_height/2),
                           window_width/6, line_thickness)
        # touchline
        touchlines = [(edge, edge),
                      (edge, window_height-edge),
                      (window_width-edge, window_height-edge),
                      (window_width-edge, edge)]
        pygame.draw.lines(window, color_line, True, touchlines, line_thickness)
        # center line
        pygame.draw.line(window, color_line,
                         (edge, window_height/2),
                         (window_width-edge, window_height/2),
                         line_thickness)
        # goal area self
        goalarea_self = [(window_width/2-goal_area_width/2, edge),
                                (window_width/2-goal_area_width/2, edge+goal_area_height),
                                (window_width/2+goal_area_width/2, edge+goal_area_height),
                                (window_width/2+goal_area_width/2, edge)]
        pygame.draw.lines(window, color_line, False, goalarea_self, line_thickness)
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

    def png_rotation_offset_x(self, png_rotation, png_width, png_length, rotation_center_x):
        rotation_rad = png_rotation/180*math.pi
        rotation_center_y = png_length - rotation_center_x
        if png_rotation == 0:
            return -rotation_center_x
        elif png_rotation > 0 and png_rotation < 90:
            return -(math.sin(rotation_rad)*rotation_center_x*(1+1/math.tan(rotation_rad)))
        elif png_rotation == 90:
            return -rotation_center_x
        elif png_rotation > 90 and png_rotation < 180:
            help_gamma = rotation_rad - math.pi / 2
            return -(png_length*math.sin(help_gamma)
                     - rotation_center_x*math.sin(help_gamma)*(1+math.tan(help_gamma))
                     + rotation_center_x/math.cos(help_gamma))
        elif png_rotation == 180:
            return -rotation_center_y
        elif png_rotation > 180 and png_rotation < 270:
            help_delta = rotation_rad - math.pi
            return -(math.cos(help_delta)*(png_length-rotation_center_x*(1+1/math.tan(help_delta)))
                     + rotation_center_x/math.sin(help_delta))
        elif png_rotation == 270:
            return -rotation_center_x
        elif png_rotation > 270 and png_rotation < 360:
            eta_help = rotation_rad - 3 / 2 * math.pi
            return -(math.sin(eta_help)*rotation_center_x*(1-math.tan(eta_help))
                     + rotation_center_x/math.cos(eta_help))

    def png_rotation_offset_y(self, png_rotation, png_width, png_length, rotation_center_x):
        rotation_rad = png_rotation/180*math.pi
        rotation_center_y = png_length - rotation_center_x
        if png_rotation == 0:
            return -rotation_center_x
        elif png_rotation > 0 and png_rotation < 90:
            return - (png_width*math.cos(rotation_rad)
                      - rotation_center_x*math.cos(rotation_rad)*(1+1/math.tan(rotation_rad))
                      + rotation_center_x/math.sin(rotation_rad))
        elif png_rotation == 90:
            return -rotation_center_x
        elif png_rotation > 90 and png_rotation < 180:
            help_gamma = rotation_rad - math.pi / 2
            return - (rotation_center_x*math.cos(help_gamma)*(1+math.tan(help_gamma)))
        elif png_rotation == 180:
            return -rotation_center_x
        elif png_rotation > 180 and png_rotation < 270:
            help_delta = rotation_rad - math.pi
            return - (png_width*math.cos(help_delta)
                      + math.sin(help_delta)*(png_length-rotation_center_x*(1+1/math.tan(help_delta))))
        elif png_rotation == 270:
            return -rotation_center_y
        elif png_rotation > 270 and png_rotation < 360:
            help_eta = rotation_rad - 3 / 2 * math.pi
            return -(png_length*math.cos(help_eta)
                     - math.cos(help_eta)*rotation_center_x*(1-math.tan(help_eta)))


    def show(self):

        GREY_DARK = (30, 30, 30)
        GREY_LIGHT = (50, 50, 50)
        BLACK = (0, 0, 0)
        WHITE = (155, 155, 155)
        ORANGE = (209, 134, 0)

        frames_per_second = 25 # Standard 25
        edge = 10
        line_thickness = 2
        window_width = self.scale(self._environment.field_length_y) + 2*edge
        window_height = self.scale(self._environment.field_length_x) + 2*edge
        robot_size_x = self.scale(self._environment.self.size_x)
        robot_size_y = self.scale(self._environment.self.size_y)
        ball_size_x = self.scale(self._environment.ball.size_x)
        goal_size_y = self.scale(self._environment.goal_self.size_y)

        pygame.init()
        pygame.display.set_caption("VectorEnvironmentViewer")
        icon = pygame.image.load("vector_icon.png")
        pygame.display.set_icon(icon)
        window = pygame.display.set_mode((window_width, window_height))
        # TODO Icon hinzufügen
        clock = pygame.time.Clock()

        self_png_rotation = 0
        self_png_rotation_offset_x = 0
        self_png_rotation_offset_y = 0
        enemy_png_rotation = 0.0
        enemy_png_rotation_offset_x = 0
        enemy_png_rotation_offset_y = 0
        robot_png_width = 25
        robot_png_length = 50
        robot_png_rotation_center_distance = robot_png_width/2
        rotation_offset = 0
        self_png = pygame.image.load("vector.png").convert_alpha()
        self_png = pygame.transform.scale(self_png, (robot_png_width, robot_png_length))
        self_png_list = []
        for i in range(0, 360, 1):
            self_png_list.append(pygame.transform.rotate(self_png, rotation_offset+i))
        enemy_png = pygame.image.load("vector.png").convert_alpha()
        enemy_png = pygame.transform.scale(enemy_png, (robot_png_width, robot_png_length))
        enemy_png_list = []
        for i in range(0, 360, 1):
            enemy_png_list.append(pygame.transform.rotate(enemy_png, rotation_offset+i))

        # Rotation Test
        # rotation = 0
        # rechteck_width = 50
        # rechteck_length = 100
        # a = rechteck_width/2
        # b = rechteck_length*0.75
        # test_rechteck = pygame.image.load("vector.png").convert_alpha()
        # test_rechteck = pygame.transform.scale(test_rechteck, (rechteck_width,rechteck_length))
        # test_rechteck_list = []
        # for i in range(0, 360, 1):
        #     test_rechteck_list.append(pygame.transform.rotate(test_rechteck, i))
        # rotation = 0
        # offset_y = 0
        # offset_x = 0

        quit = False

        while not quit:

            for event in pygame.event.get():
                if event.type == QUIT:
                    quit = True
            
            self.draw_field(window, window_height, window_width,
                        edge, line_thickness, goal_size_y,
                        GREY_DARK, GREY_LIGHT, BLACK)

            self_position_x = self.scale(self._environment.self.position_x)
            self_position_y = self.scale(self._environment.self.position_y)
            self_rotation = round(self._environment.self.rotation) + 180
            enemy_position_x = self.scale(self._environment.enemy.position_x)
            enemy_position_y = self.scale(self._environment.enemy.position_y)
            enemy_rotation = self._environment.enemy.rotation + 180
            ball_position_x = self.scale(self._environment.ball.position_x)
            ball_position_y = self.scale(self._environment.ball.position_y)

            # Draw Ball
            pygame.draw.circle(window,
                               ORANGE,
                               (ball_position_y + edge,
                                ball_position_x + edge),
                               ball_size_x/2)
            # Draw Self
            self_png_rotation_offset_y = self.png_rotation_offset_y(self_rotation, robot_png_width, robot_png_length, robot_png_rotation_center_distance)
            self_png_rotation_offset_x = self.png_rotation_offset_x(self_rotation, robot_png_width, robot_png_length, robot_png_rotation_center_distance)
            self_png = self_png_list[self_rotation]
            window.blit(self_png, (self_position_y + self_png_rotation_offset_y + edge,
                                   self_position_x + self_png_rotation_offset_x + edge))

            # Rotation Test
            # if rotation <= 360:
            #     test_rechteck = test_rechteck_list[rotation]
            # rotation_rad = rotation/180*math.pi
            # if rotation == 0:
            #     offset_y = -a
            #     offset_x = -a
            # elif rotation > 0 and rotation < 90:
            #     offset_y = - (rechteck_width*math.cos(rotation_rad)
            #                   -a*math.cos(rotation_rad)*(1+1/math.tan(rotation_rad))
            #                   + a/math.sin(rotation_rad))
            #     offset_x = - (math.sin(rotation_rad)*a*(1+1/math.tan(rotation_rad)))
            # elif rotation == 90:
            #    offset_y = -a
            #    offset_x = -a
            # elif rotation > 90 and rotation < 180:
            #     gamma = rotation_rad - math.pi / 2
            #     offset_y = - (a*math.cos(gamma)*(1+math.tan(gamma)))
            #     offset_x = - (rechteck_length*math.sin(gamma)
            #                   - a*math.sin(gamma)*(1+math.tan(gamma))
            #                   + a/math.cos(gamma))
            # elif rotation == 180:
            #     offset_y = -a
            #     offset_x = -b
            # elif rotation > 180 and rotation < 270:
            #     delta = rotation_rad - math.pi
            #     offset_y = - (rechteck_width*math.cos(delta)
            #                  +math.sin(delta)*(rechteck_length-a*(1+1/math.tan(delta))))
            #     offset_x = - (math.cos(delta)*(rechteck_length-a*(1+1/math.tan(delta)))
            #                   + a/math.sin(delta))
            # elif rotation == 270:
            #     offset_y = -b
            #     offset_x = -a
            # elif rotation > 270 and rotation < 360:
            #     eta = rotation_rad - 3 / 2 * math.pi
            #     offset_y = -(rechteck_length * math.cos(eta)
            #                  - math.cos(eta) * a *(1-math.tan(eta)) )
            #     offset_x = -(math.sin(eta)*a*(1-math.tan(eta))
            #                  +a / math.cos(eta))
            # print(f"Rot:{rotation}, x:{offset_x}, y:{offset_y}")
            # window.blit(test_rechteck, (window_width/2 + offset_y,
            #                             window_height/2 + offset_x))
            # rotation = rotation + 1

            # Draw Enemy
            # enemy_png = enemy_png_list[enemy_rotation]
            # window.blit(enemy_png, (enemy_position_y - robot_size_y*0.7 + edge,
            #                         enemy_position_x - robot_size_x/2 + edge))

            # print(f'Viewer: Self:{round(self_position_x*3)},{round(self_position_y*3)}'
            #       f'Painted Ball at {round(ball_position_x*3)},{ball_position_y*3}')

            pygame.display.update()
            clock.tick(frames_per_second)

        pygame.quit()


class EnvironmentTest():

    def test_viewer(self, environment):
        print('+++ViewerTest+++')
        environment_viewer = EnvironmentViewer(environment)
        environment_viewer.show()

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
            robot = anki_vector.Robot(serial=SERIAL_VINCENT,
                                      behavior_control_level=ControlPriorityLevel.OVERRIDE_BEHAVIORS_PRIORITY)
            environment = Environment(robot,
                                      field_length_x=1600.0,
                                      field_length_y=1000.0,
                                      goal_width=200.0,
                                      ball_diameter=40.0,
                                      position_start_x=150.0,
                                      position_start_y=500.0)
            robot.connect()
            robot.behavior.set_eye_color(0.05, 1.0)  # Augenfarbe orange

            # self.test_general(robot, environment)
            # self.test_winkelformat(robot, environment)
            # self.test_proximity(robot, environment)
            self.test_viewer(environment)

            robot.disconnect()

        else:
            robot = None
            environment = Environment(robot,
                                      field_length_x=1600.0,
                                      field_length_y=1000.0,
                                      goal_width=200.0,
                                      ball_diameter=40.0,
                                      position_start_x=150.0,
                                      position_start_y=500.0)
            self.test_viewer(environment)


if __name__ == '__main__':
    environment_test = EnvironmentTest()
    environment_test.test()
