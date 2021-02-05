import anki_vector
import time
from anki_vector.connection import ControlPriorityLevel
from anki_vector.util import degrees, Pose
from anki_vector import behavior
import pygame
# from pygame.constants import K_0
from pygame.locals import Rect, QUIT
import threading
import math
import anki_vector.events
from anki_vector.events import Events
import pandas
import matplotlib.pyplot as plot
import statsmodels.api as statsmodels
from scipy import stats

NAME = 'Vector-N8G2'
NAME_VINCENT = 'Vector-R7U1'
IP_VINCENT = '192.168.68.142'
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
        self._offset_x = 0
        self._offset_y = 0

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
            self._self.position_x = position_x + self._POSITION_START_X + self.offset_x
            self._self.position_y = position_y + self._POSITION_START_Y + self.offset_y
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
    
    @property
    def offset_x(self):
        return self._offset_x

    @offset_x.setter
    def offset_x(self, offset_x):
        self._offset_x = offset_x

    @property
    def offset_y(self):
        return self._offset_y

    @offset_y.setter
    def offset_y(self, offset_y):
        self._offset_y = offset_y


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
        self._last_known_positions_x = {}
        self._last_known_positions_y = {}

    def pose(self):
        if self._tag == 'Self':
            position_x = self._robot.pose.to_matrix().pos_xyz[0]
            position_y = self._robot.pose.to_matrix().pos_xyz[1]
            rotation = self._robot.pose_angle_rad / math.pi * 180.0
            self._self.position_x = position_x + self._POSITION_START_X
            self._self.position_y = position_y + self._POSITION_START_Y
            self._self.rotation = rotation
            self._self.last_seen = time.time()
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
        '''Sets the last seen time, saves the current position
        with the time in the last known positions
        and deletes the position 10 seconds ago.
        '''
        self._last_seen = int(last_seen)
        self.last_known_positions_x.update({last_seen: self.position_x})
        self.last_known_positions_y.update({last_seen: self.position_y})
        time_threshold = 10
        self.last_known_positions_x.pop(last_seen-time_threshold, 'empty_msg')
        self.last_known_positions_y.pop(last_seen-time_threshold, 'empty_msg')

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

    @property
    def last_known_positions_x(self):
        return self._last_known_positions_x

    @property
    def last_known_positions_y(self):
        return self._last_known_positions_y


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
                   color_field,
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
        pygame.draw.rect(window, color_field, rect_field)
        # goal self
        rect_goal_self = Rect(window_width/2 - goal_size_y/2,
                              edge-20,
                              goal_size_y,
                              20)
        pygame.draw.rect(window, color_goal, rect_goal_self)
        # goal enemy
        rect_goal_enemy = Rect(window_width/2 - goal_size_y/2,
                               window_height-edge,
                               goal_size_y,
                               20)
        pygame.draw.rect(window, color_goal, rect_goal_enemy)
        # center circle
        pygame.draw.circle(window, color_line,
                           (window_width/2, window_height/2),
                           50, line_thickness)
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

    def png_rotation_offset_x(self, png_rotation,
                              png_width, png_length, rotation_center_x):
        rotation_rad = png_rotation/180*math.pi
        rotation_center_y = png_length - rotation_center_x
        if png_rotation == 0 or png_rotation == 360:
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

    def png_rotation_offset_y(self, png_rotation,
                              png_width, png_length, rotation_center_x):
        rotation_rad = png_rotation/180*math.pi
        rotation_center_y = png_length - rotation_center_x
        if png_rotation == 0 or png_rotation == 360:
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

    def blit_environment_object(self, object, window, png_width, png_length,
                                png_center_x, rotation_png_list, edge=0):
        position_x = self.scale(object.position_x)
        position_y = self.scale(object.position_y)
        if object is self._environment.ball:
            rotation = 0
        else:
            rotation = round(object.rotation) + 180
        png_rotation_offset_y = self.png_rotation_offset_y(rotation,
                                                           png_width,
                                                           png_length,
                                                           png_center_x)
        png_rotation_offset_x = self.png_rotation_offset_x(rotation,
                                                           png_width,
                                                           png_length,
                                                           png_center_x)
        png = rotation_png_list[rotation]
        if (object == self._environment.ball) or (object == self._environment.enemy):
            now = int(time.time())
            last_seen = object.last_seen
            if last_seen == 0:
                opacity = 255
            elif (now-last_seen) <= 10:
                opacity = int((1-(now-last_seen)/(10))*255)
            else:
                opacity = 0
            png.set_alpha(opacity)
            if last_seen != 0:
                position_x = object.last_known_positions_x.get(last_seen, position_x) # TODO überprüfen ob es funktioniert
                position_y = object.last_known_positions_y.get(last_seen, position_y)
        window.blit(png, (position_y + png_rotation_offset_y + edge,
                          position_x + png_rotation_offset_x + edge))   

    def draw_environment_object(self, object, color,
                                size_x, size_y, window, edge=0):
        position_x = self.scale(object.position_x)
        position_y = self.scale(object.position_y)
        if object.tag == 'Ball':
            pygame.draw.circle(window,
                               color,
                               (position_y + edge,
                                position_x + edge),
                                size_x/2)

    def object_identical(self, object_position_x, object_position_y,
                         environment_object):
        '''Returns whether one object is identical to an
        EnvrionmentObject using both objects position
        and the last positions of the environment object
        '''
        object_identical = False
        now = int(time.time())
        threshold_distance_x = self.scale(environment_object.size_x)*2
        threshold_distance_y = self.scale(environment_object.size_y)*2
        last_known_positions_x = environment_object.last_known_positions_x
        last_known_positions_y = environment_object.last_known_positions_y
        for moment in range(now, now-10, -1):
            if last_known_positions_x.get(moment, False) is not False:
                environment_object_position_x = self.scale(last_known_positions_x[moment])
                environment_object_position_y = self.scale(last_known_positions_y[moment])
                if (object_position_x >= environment_object_position_x-threshold_distance_x
                    and object_position_x <= environment_object_position_x+threshold_distance_x
                    and object_position_y >= environment_object_position_y-threshold_distance_y
                    and object_position_y <= environment_object_position_y+threshold_distance_y):
                    object_identical = True
        return object_identical

    def robot_picked_up(self, robot, origin_id):
        if robot is not None:
            return (origin_id != robot.pose.origin_id)
        else:
            return False

    def object_is_environment_object(self, object_position_y, object_position_x, ball, enemy, goal_self, goal_enemy):
        object_is_ball = self.object_identical(object_position_x, object_position_y, ball)
        object_is_enemy = self.object_identical(object_position_x, object_position_y, enemy)
        object_is_goal_self = self.object_identical(object_position_x, object_position_y, goal_self)
        object_is_goal_enemy = self.object_identical(object_position_x, object_position_y, goal_enemy)
        return (object_is_ball
                or object_is_enemy
                or object_is_goal_self
                or object_is_goal_enemy)

    def object_close_to_wall(self, object_position_x, object_position_y, window_height, window_width):
        return ((object_position_x <= window_height*0.35 or object_position_x >= window_height*0.65)
                and (object_position_y <= window_width*0.35 or object_position_y >= window_width*0.65))

    def translate_environment(self, object_position_y, object_position_x):
        distance_to_wall_north = self.scale(self._environment.field_length_x) - object_position_x
        distance_to_wall_south = object_position_x
        distance_to_wall_east = object_position_y
        distance_to_wall_west = self.scale(self._environment.field_length_y) - object_position_y
        distances_to_walls = (distance_to_wall_north, distance_to_wall_south, distance_to_wall_east, distance_to_wall_west)
        if min(distances_to_walls) == distance_to_wall_north:
            self._environment.offset_x = distance_to_wall_north*3
            print(f"x um {distance_to_wall_north*3} verschoben.")
        if min(distances_to_walls) == distance_to_wall_south:
            self._environment.offset_x = -distance_to_wall_south*3
            print(f"x um {-distance_to_wall_south*3} verschoben.")
        if min(distances_to_walls) == distance_to_wall_west:
            self._environment.offset_y = distance_to_wall_west*3
            print(f"y um {distance_to_wall_west*3} verschoben.")
        if min(distances_to_walls) == distance_to_wall_east:
            self._environment.offset_y = -distance_to_wall_east*3
            print(f"y um {-distance_to_wall_east*3} verschoben.")

    def translate_observed_points(self, object_position_y, object_position_x, observed_points):
        distance_to_wall_north = self.scale(self._environment.field_length_x) - object_position_x
        distance_to_wall_south = object_position_x
        distance_to_wall_east = object_position_y
        distance_to_wall_west = self.scale(self._environment.field_length_y) - object_position_y
        distances_to_walls = (distance_to_wall_north, distance_to_wall_south, distance_to_wall_east, distance_to_wall_west) 
        observed_points_y = []
        observed_points_x = []
        observed_points_new = []
        for points in observed_points:
            observed_points_y.append(points[0])
            observed_points_x.append(points[1])
        if min(distances_to_walls) == distance_to_wall_north:
            for i in range(0, len(observed_points)):
                observed_points_new.append((observed_points_y[i], observed_points_x[i]+distance_to_wall_north))
        if min(distances_to_walls) == distance_to_wall_south:
            for i in range(0, len(observed_points)):
                observed_points_new.append((observed_points_y[i], observed_points_x[i]-distance_to_wall_south))
        if min(distances_to_walls) == distance_to_wall_west:
            for i in range(0, len(observed_points)):
                observed_points_new.append((observed_points_y[i]+distance_to_wall_west, observed_points_x[i]))
        if min(distances_to_walls) == distance_to_wall_east:
            for i in range(0, len(observed_points)):
                observed_points_new.append((observed_points_y[i]-distance_to_wall_east, observed_points_x[i]))
        return observed_points_new
        # distance_to_wall_north = self.scale(self._environment.field_length_x) - object_position_x
        # distance_to_wall_south = object_position_x
        # distance_to_wall_east = object_position_y
        # distance_to_wall_west = self.scale(self._environment.field_length_y) - object_position_y
        # distances_to_walls = (distance_to_wall_north, distance_to_wall_south, distance_to_wall_east, distance_to_wall_west) 
        # observed_points_y = []
        # observed_points_x = []
        # observed_points_new = []
        # for points in observed_points:
        #     observed_points_y.append(points[0])
        #     observed_points_x.append(points[1])
        # if min(distances_to_walls) == distance_to_wall_north:
        #     self._environment.offset_x = distance_to_wall_north*3
        #     for i in range(0, len(observed_points)):
        #         observed_points_new.append((observed_points_y[i], observed_points_x[i]+distance_to_wall_north))
        #     print(f"x um {distance_to_wall_north*3} verschoben.")
        # if min(distances_to_walls) == distance_to_wall_south:
        #     self._environment.offset_x = -distance_to_wall_south*3
        #     for i in range(0, len(observed_points)):
        #         observed_points_new.append((observed_points_y[i], observed_points_x[i]-distance_to_wall_south))
        #     print(f"x um {-distance_to_wall_south*3} verschoben.")
        # if min(distances_to_walls) == distance_to_wall_west:
        #     self._environment.offset_y = distance_to_wall_west*3
        #     for i in range(0, len(observed_points)):
        #         observed_points_new.append((observed_points_y[i]+distance_to_wall_west, observed_points_x[i]))
        #     print(f"y um {distance_to_wall_west*3} verschoben.")
        # if min(distances_to_walls) == distance_to_wall_east:
        #     self._environment.offset_y = -distance_to_wall_east*3
        #     for i in range(0, len(observed_points)):
        #         observed_points_new.append((observed_points_y[i]-distance_to_wall_east, observed_points_x[i]))
        #     print(f"y um {-distance_to_wall_east*3} verschoben.")
        # observed_points = observed_points_new

    def delete_repetetive_points(self, point_list):
        threshold = 5
        for point_a in point_list:
            for point_b in point_list:
                if point_a != point_b:
                    if abs(point_a[0]-point_b[0]) <= threshold and abs(point_a[1]-point_b[1]) <= threshold:
                        point_list.remove(point_b)
        return point_list

    def show(self, show_self=True, show_ball=True, show_enemy=True, automatic_map_transformation=False):
        GREY_DARK = (20, 20, 20)
        GREY_MEDIUM = (40, 40, 40)
        GREY_LIGHT = (50, 50, 50)
        BLACK = (0, 0, 0)
        WHITE = (155, 155, 155)
        ORANGE = (209, 134, 0)

        frames_per_second = 30
        edge = 35
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
        clock = pygame.time.Clock()

        robot_png_width = 25
        robot_png_length = 50
        robot_png_center_x = robot_png_width/2
        robot_png = pygame.image.load("vector.png").convert_alpha()
        robot_png = pygame.transform.scale(robot_png,
                                           (robot_png_width, robot_png_length))
        robot_png_list = []
        for angle in range(0, 361, 1):
            robot_png_list.append(pygame.transform.rotate(robot_png, angle))

        ball_png_width = ball_size_x
        ball_png_length = ball_size_x
        ball_png_center_x = ball_png_width/2
        ball_png = pygame.image.load("ball.png").convert_alpha()
        ball_png = pygame.transform.scale(ball_png,
                                          (ball_png_width, ball_png_length))
        ball_png_list = []
        for angle in range(0, 361, 1):
            ball_png_list.append(ball_png)

        # Edge detection
        suspicious_points = []
        observed_points = []
        observed_points_from_one_line = []
        observed_lines = []
        frames_left_to_observe_one_line = 0
        robot = self._environment.robot
        goal_self = self._environment.goal_self
        goal_enemy = self._environment.goal_enemy
        observing_line = False
        # Edge detection

        if robot is None:
            origin_id = 0
        else:
            origin_id = robot.pose.origin_id
        font = pygame.font.Font(None, 24)
        reset_warning = "Vector picked up. Coordinate system reset."
        reset_text = font.render(reset_warning, 1, BLACK, WHITE)
        reset_text_size_y = font.size(reset_warning)[0]
        reset_text_size_x = font.size(reset_warning)[1]
        reset_text_position = (window_width/2-reset_text_size_y/2,
                               window_height/2-reset_text_size_x/2)
        frames_left_reset_text = 0

        quit = False
        while not quit:

            for event in pygame.event.get():
                if event.type == QUIT:
                    quit = True

            self.draw_field(window, window_height, window_width,
                            edge, line_thickness, goal_size_y, GREY_DARK,
                            GREY_MEDIUM, GREY_LIGHT, GREY_MEDIUM)
            
            robot_self = self._environment.self
            if show_self:
                self.blit_environment_object(robot_self, window,
                                             robot_png_width,
                                             robot_png_length,
                                             robot_png_center_x,
                                             robot_png_list, edge)

            ball = self._environment.ball
            if show_ball:
                # self.draw_environment_object(ball, ORANGE,
                #                              ball_size_x, ball_size_x,
                #                              window, edge)
                self.blit_environment_object(ball, window,
                                             ball_png_width,
                                             ball_png_length,
                                             ball_png_center_x,
                                             ball_png_list, edge)

            robot_enemy = self._environment.enemy
            if show_enemy:
                self.blit_environment_object(robot_enemy, window,
                                             robot_png_width,
                                             robot_png_length,
                                             robot_png_center_x,
                                             robot_png_list, edge)

            if automatic_map_transformation == True:
                # Edge detection
                self_position_x = self.scale(robot_self.position_x)
                self_position_y = self.scale(robot_self.position_y)    
                self_rotation_rad = round(robot_self.rotation) / 180 * math.pi
                # Find objects
                if robot is not None:
                    proximity_data = robot.proximity.last_sensor_reading
                    if proximity_data is not None and proximity_data.found_object:
                        object_distance = self.scale(proximity_data.distance.distance_mm)
                        object_position_x = self_position_x + object_distance * math.cos(self_rotation_rad)
                        object_position_y = self_position_y + object_distance * math.sin(self_rotation_rad)
                        object_is_environment_object = self.object_is_environment_object(object_position_x, object_position_y, ball, robot_enemy, goal_self, goal_enemy)
                        object_is_wall = not object_is_environment_object
                        if object_is_wall:
                            object_close_to_wall = self.object_close_to_wall(object_position_x, object_position_y, window_height, window_width)
                            if not object_close_to_wall:
                                observed_points.append((object_position_y, object_position_x))
                            else:
                                observed_points.append((object_position_y, object_position_x))
                                self.translate_environment(object_position_y, object_position_x)
                                observed_points = self.translate_observed_points(object_position_y, object_position_x, observed_points)
                            if observing_line:  # OR if vector is turning right now
                                observed_points_from_one_line.append((object_position_y, object_position_x))
                            else:
                                observed_points_from_one_line.append((object_position_y, object_position_x))
                                seconds_left_to_observe_line = 3
                                frames_left_to_observe_one_line = seconds_left_to_observe_line * frames_per_second
                                observing_line = True
                # Filter data
                observed_points = self.delete_repetetive_points(observed_points)
                # Choose more than 10 points that form a line
                # minimum_points_for_line = 10
                # if len(observed_points) > 5:
                #     pass
                # choose points so that
                # either the x value is alternating not much and the y value is (standarderror)
                # for i in range(1,100):
                #     points_picked = []
                #     points_picked.append(points_observed[])
                # if standard_error_x < 10 and standard_error_y > 10
                # or the y value is alternating not much and the x value is
                # if line_points_# wenn punkte aus
                # len(observed_points) > 5: # if there are enough points to form a line, that have a specific distance
                    # PSEUDOCODE
                    # if len(suspicious_points) > 5 and suspicious_points_form-line:
                    #     if distance to next wall is close_to_wall_if_map_is_turned:
                    #         turn.map(estimated rotation)
                # Look for lines
                if frames_left_to_observe_one_line == 0 and observing_line:
                    print('Finished observing points.')
                    if len(observed_points_from_one_line >= 5):
                        print('Enough points observed!')
                        line_points_x = []
                        line_points_y = []
                        for point in observed_points_from_one_line:
                            line_points_x.append(point[1])
                            line_points_y.append(point[0])
                        slope, intercept, r, p, std_err = stats.linregress(line_points_x, line_points_y)
                        # y = intercept + x * slope
                        new_line = ((0 * slope + intercept, 0),
                                    (window_height * slope + intercept, window_height))
                        observed_points_from_one_line.clear()
                        observed_lines.append(new_line)
                    observing_line = False
                    # found line is a regression of found points (some threshold needed and something to determine which point belongs to which line)
                    # Remember the last two lines that have an angle close to 90 degrees
                    if frames_left_to_observe_one_line != 0:
                        frames_left_to_observe_one_line -= 1
                    # print(f'Objekt gefunden {proximity_data.distance.distance_mm}mm vor Vector.')
            
            for line in observed_lines:
                pygame.draw.line(window, WHITE, (line[0][0]+edge, line[0][1]+edge), (line[1][0]+edge, line[1][1]+edge), 1)
            for point in observed_points:
                pygame.draw.circle(window, BLACK, (point[0]+edge, point[1]+edge), 3)
            # Edge detection

            if self.robot_picked_up(robot, origin_id):
                    origin_id += 1
                    seconds_left_reset_text = 2
                    frames_left_reset_text = seconds_left_reset_text*frames_per_second
                    self._environment.offset_x = 0
                    self._environment.offset_y = 0
                    observed_points.clear()
                    observed_lines.clear()
                    robot_self.last_known_positions_x.clear()
                    robot_self.last_known_positions_y.clear()
                    robot_enemy.last_known_positions_x.clear()
                    robot_enemy.last_known_positions_y.clear()
                    ball.last_known_positions_x.clear()
                    ball.last_known_positions_y.clear()
            if frames_left_reset_text > 0:
                window.blit(reset_text, reset_text_position)
                frames_left_reset_text -= 1

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

    def test_rotation(self):
        # Rotation Test vor Loop
        rotation = 0
        rechteck_width = 50
        rechteck_length = 100
        a = rechteck_width/2
        b = rechteck_length*0.75
        test_rechteck = pygame.image.load("vector.png").convert_alpha()
        test_rechteck = pygame.transform.scale(test_rechteck, (rechteck_width,rechteck_length))
        test_rechteck_list = []
        for i in range(0, 360, 1):
            test_rechteck_list.append(pygame.transform.rotate(test_rechteck, i))
        rotation = 0
        offset_y = 0
        offset_x = 0
        # Rotation Test in Loop
        if rotation <= 360:
            test_rechteck = test_rechteck_list[rotation]
        rotation_rad = rotation/180*math.pi
        if rotation == 0:
            offset_y = -a
            offset_x = -a
        elif rotation > 0 and rotation < 90:
            offset_y = - (rechteck_width*math.cos(rotation_rad)
                            -a*math.cos(rotation_rad)*(1+1/math.tan(rotation_rad))
                            + a/math.sin(rotation_rad))
            offset_x = - (math.sin(rotation_rad)*a*(1+1/math.tan(rotation_rad)))
        elif rotation == 90:
            offset_y = -a
            offset_x = -a
        elif rotation > 90 and rotation < 180:
            gamma = rotation_rad - math.pi / 2
            offset_y = - (a*math.cos(gamma)*(1+math.tan(gamma)))
            offset_x = - (rechteck_length*math.sin(gamma)
                            - a*math.sin(gamma)*(1+math.tan(gamma))
                            + a/math.cos(gamma))
        elif rotation == 180:
            offset_y = -a
            offset_x = -b
        elif rotation > 180 and rotation < 270:
            delta = rotation_rad - math.pi
            offset_y = - (rechteck_width*math.cos(delta)
                            +math.sin(delta)*(rechteck_length-a*(1+1/math.tan(delta))))
            offset_x = - (math.cos(delta)*(rechteck_length-a*(1+1/math.tan(delta)))
                            + a/math.sin(delta))
        elif rotation == 270:
            offset_y = -b
            offset_x = -a
        elif rotation > 270 and rotation < 360:
            eta = rotation_rad - 3 / 2 * math.pi
            offset_y = -(rechteck_length * math.cos(eta)
                            - math.cos(eta) * a *(1-math.tan(eta)) )
            offset_x = -(math.sin(eta)*a*(1-math.tan(eta))
                            +a / math.cos(eta))
        print(f"Rot:{rotation}, x:{offset_x}, y:{offset_y}")
        window.blit(test_rechteck, (window_width/2 + offset_y,
                                    window_height/2 + offset_x))
        rotation = rotation + 1

    def test(self):
        anki_vector_available = True
        if anki_vector_available is True:
            robot = anki_vector.Robot(serial=SERIAL_VINCENT) # Vielleicht mit behavior_control_level=ControlPriorityLevel.OVERRIDE_BEHAVIORS_PRIORITY
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
