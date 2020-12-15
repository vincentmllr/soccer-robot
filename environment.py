import anki_vector, multiprocessing, time
from anki_vector.util import degrees, Pose
from anki_vector import behavior

NAME = 'Vector-N8G2'
IP = '192.168.0.189'
SERIAL = '008014c1'

class Environment():
    '''Representation of vectors environment/ the soccer field with all its objects and function to return those objects.
    '''

    FIELD_LENGTH_X = 2000.0
    FIELD_LENGTH_Y = 1000.0
    field_height = 150.0 #Nicht benutzt
    wall_thickness = 10.0 #Nicht benutzt
    goal_width = 200.0 #Nicht benutzt
    goal_height = 100.0 #Nicht benutzt
    POSITION_START_X = 100.0
    POSITION_START_Y = 500.0
    
    def __init__(self, robot):
        self._robot = robot
        self._self = EnvironmentObject('Self', self.POSITION_START_X, self.POSITION_START_Y, degrees(0), 0, self)
        self._ball = EnvironmentObject('Ball', (self.FIELD_LENGTH_X)/2, self.POSITION_START_Y, degrees(0), 0, self)
        self._enemy = EnvironmentObject('Enemy', self.FIELD_LENGTH_X-self.POSITION_START_X, self.POSITION_START_Y, degrees(0), 0, self)
        self._goal_self = EnvironmentObject('Goal_self', 0, self.POSITION_START_Y, degrees(0), 0, self)
        self._goal_enemy = EnvironmentObject('Goal_enemy', self.FIELD_LENGTH_X, self.POSITION_START_Y, degrees(0), 0, self)
        print('Environment initialized with objects in startposition')

    def environment_update(self):
        '''Returns a list of all the objects on the map in the following order: Self, ball, enemy, goal_enemy, goal_self as EnvironmentObjects
        '''
        return [self.self, self._ball, self._enemy, self._goal_enemy, self._goal_self]
    
    @property
    def self(self):
        self.self.position_x = self.robot.pose.position.to_matrix.pos_xyz[0] - self.POSITION_START_X
        self.self.position_y = self.robot.pose.position.to_matrix.pos_xyz[1] - self.POSITION_START_Y
        self.self.rotation = self.robot.pose_angle_rad
        print(f'Updated {self._self.tag} position.')
        return self.self

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

class EnvironmentObject():

    def __init__(self, tag, position_x, position_y, rotation, time, environment):
        self._tag = tag
        self._position_x = position_x  - environment.POSITION_START_X
        self._position_y = position_y - environment.POSITION_START_Y
        self._rotation = rotation #in Grad
        self._moment = time
        self._environment = environment
       
    def pose(self):
        if self._tag == 'Self':
            self.position_x = self._environment.robot.pose.position.to_matrix.pos_xyz[0] - self._environment.POSITION_START_X
            self.position_y = self._environment.robot.pose.position.to_matrix.pos_xyz[1] - self._environment.POSITION_START_Y
            self.rotation = self._environment.robot.pose_angle_rad
            print(f'Updated {self._tag} position.')
            return Pose(x=self.position_x, y=self.position_y, z=0, angle_z=anki_vector.util.Angle(degrees=self._rotation))
        else:
            return Pose(x=self.position_x, y=self.position_y, z=0, angle_z=anki_vector.util.Angle(degrees=0))

    @property
    def tag(self):
        return self._tag
    
    @property
    def position_x(self):
        return self._position_x

    @position_x.setter
    def position_x(self, position_x):
        self._position_x = position_x - self._environment.POSITION_START_X

    @property
    def position_y(self):
        return self._position_y

    @position_y.setter
    def position_y(self, position_y):
        self._position_y = position_y - self._environment.POSITION_START_Y

    @property
    def rotation(self):
        return self._rotation()
    
    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation
    
    @property
    def last_updated(self):
        return self._moment

    @property
    def environment(self):
        return self._environment


def test_custom_object(robot, environment):
    print('+++CustomObject-Test+++')
    #Erstellt die Wände
    wall_left = robot.world.create_custom_fixed_object(
        Pose(x=-environment.POSITION_START_X, y=environment.POSITION_START_Y, z=0, angle_z=degrees(0)), 
        x_size_mm=environment.field_length, 
        y_size_mm=environment.wall_thickness, 
        z_size_mm=environment.field_height,
        relative_to_robot=True)
    wall_right = robot.world.create_custom_fixed_object(
        Pose(x=-environment.POSITION_START_X, y=-environment.POSITION_START_Y, z=0, angle_z=degrees(0)), 
        x_size_mm=environment.field_length, 
        y_size_mm=environment.wall_thickness, 
        z_size_mm=environment.field_height,
        relative_to_robot=True)
    wall_self = robot.world.create_custom_fixed_object(
        Pose(x=-environment.POSITION_START_X, y=-environment.POSITION_START_Y, z=0, angle_z=degrees(90)), 
        x_size_mm=environment.field_width, 
        y_size_mm=environment.wall_thickness, 
        z_size_mm=environment.field_height,
        relative_to_robot=True)
    wall_oponent = robot.world.create_custom_fixed_object(
        Pose(x=-environment.POSITION_START_X, y=environment.field_length-environment.POSITION_START_Y, z=0, angle_z=degrees(90)), 
        x_size_mm=environment.field_width, 
        y_size_mm=environment.wall_thickness, 
        z_size_mm=environment.field_height,
        relative_to_robot=True)  
    print("Alle Objekte:")
    for obj in robot.world.all_objects:
        print(obj)  

    
def test_proximity(robot,environment):
    print("+++Proximity-Test:+++")
    for i in range(1,10):
        proximity_data=robot.proximity.last_sensor_reading
        if proximity_data is not None:
            print('Proximity distance: {0}' .format(proximity_data))
        print(proximity_data.distance)
        print(proximity_data.found_object)
        print(proximity_data.is_lift_in_fov)
        print(proximity_data.signal_quality)
        print(proximity_data.unobstructed)


def test_general(robot, environment):
    print("Grundtest gestartet")
    test_done = False
    print("Fahre zum Startpunkt...")
    robot.behavior.go_to_pose(environment.self.pose(), False, 3)
    while robot.accel != 0 and test_done == False :
        print(f"Beim Startpunkt ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
        print("Fahre zum _Ball...")
        robot.behavior.go_to_pose(environment._ball.pose(), False, 3)
        while robot.accel != 0 and test_done == False :
            print(f"Beim _Ball ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
            print("Fahre zum Gegner...")
            robot.behavior.go_to_pose(environment._enemy.pose(), False, 3)
            while robot.accel != 0 and test_done == False :
                print(f"Beim Gegner ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
                print("Fahre zum eigenen Tor...")
                robot.behavior.go_to_pose(environment._goal_self.pose(), False, 3)
                while robot.accel != 0 and test_done == False :
                    print(f"Beim eigenen Tor ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
                    print("Fahre zum gegenerischen Tor...")
                    robot.behavior.go_to_pose(environment.goal__enemy.pose(), False, 3)
                    while robot.accel != 0 and test_done == False :
                        print(f"Beim gegnerischen Tor ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
                        test_done = True

def test_winkelformat(robot, environment):
    print(f'+++Winkelformatvergleich+++')
    print(f'Angle(): {anki_vector.util.Angle(degrees=0)}')
    print(f'degrees(): {degrees(environment._enemy.rotation)}')
    print(f'Angle(rotation): {anki_vector.util.Angle(degrees=environment.self.rotation)}')


def test():

    environment = Environment()
    robot = anki_vector.Robot(serial = SERIAL)
    robot.connect()
    robot.behavior.set_eye_color(0.05, 1.0) #Augenfarbe orange

    with behavior.ReserveBehaviorControl(serial= SERIAL):

        #test_general(robot, environment)
        test_winkelformat(robot, environment)
        #test_proximity(robot, environment)
        #test_custom_object(robot, environment)

    robot.disconnect()


   
if __name__ == '__main__':
    test()

