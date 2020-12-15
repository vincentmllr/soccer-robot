import anki_vector, multiprocessing, time
from anki_vector.util import degrees, Pose
from anki_vector import behavior

NAME = "Vector-N8G2"
IP = "192.168.0.189"
SERIAL = "008014c1"

class Environment():
    """Representation of vectors environment/ the soccer field with all its objects.
    """

    FIELD_LENGTH_X = 2000.0
    FIELD_LENGTH_Y = 1000.0
    field_height = 150.0 #Nicht benutzt
    wall_thickness = 10.0 #Nicht benutzt
    goal_width = 200.0 #Nicht benutzt
    goal_height = 100.0 #Nicht benutzt
    POSITION_START_X = 100.0
    POSITION_START_Y = 500.0
    
    def __init__(self):
        self.self = EnvironmentObject("Self", self.POSITION_START_X, self.POSITION_START_Y, degrees(0), 0, self)
        self.ball = EnvironmentObject("Ball", (self.FIELD_LENGTH_X)/2, self.POSITION_START_Y, degrees(0), 0, self)
        self.enemy = EnvironmentObject("Enemy", self.FIELD_LENGTH_X-self.POSITION_START_X, self.POSITION_START_Y, degrees(0), 0, self)
        self.goal_self = EnvironmentObject("Goal_self", 0, self.POSITION_START_Y, degrees(0), 0, self)
        self.goal_enemy = EnvironmentObject("Goal_enemy", self.FIELD_LENGTH_X, self.POSITION_START_Y, degrees(0), 0, self)

    def environment_update(self):
        '''Returns a list of all the objects on the map in the following order: Self, ball, enemy, goal_enemy, goal_self as EnvironmentObjects
        '''
        return [self.self, self.ball, self.enemy, self.goal_enemy, self.goal_self]
    

class EnvironmentObject():

    def __init__(self, tag, position_x, position_y, rotation, time, environment):
        self.tag = tag
        self.position_x = position_x  - environment.POSITION_START_X
        self.position_y = position_y - environment.POSITION_START_Y
        self.rotation = rotation #in Grad
        self.moment = time
        self.environment = environment
        
    
    def pose(self):
        return Pose(x=self.position_x, y=self.position_y, z=0, angle_z=anki_vector.util.Angle(degrees=0))


def test_custom_object(robot, environment):
    print("+++CustomObject-Test+++")
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
    while robot.accel != 0 & test_done == False :
        print(f"Beim Startpunkt ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
        print("Fahre zum Ball...")
        robot.behavior.go_to_pose(environment.ball.pose(), False, 3)
        while robot.accel != 0 & test_done == False :
            print(f"Beim Ball ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
            print("Fahre zum Gegner...")
            robot.behavior.go_to_pose(environment.enemy.pose(), False, 3)
            while robot.accel != 0 & test_done == False :
                print(f"Beim Gegner ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
                print("Fahre zum eigenen Tor...")
                robot.behavior.go_to_pose(environment.goal_self.pose(), False, 3)
                while robot.accel != 0 & test_done == False :
                    print(f"Beim eigenen Tor ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
                    print("Fahre zum gegenerischen Tor...")
                    robot.behavior.go_to_pose(environment.goal_enemy.pose(), False, 3)
                    while robot.accel != 0 & test_done == False :
                        print(f"Beim gegnerischen Tor ({robot.pose.to_matrix().pos_xyz[0]},{robot.pose.to_matrix().pos_xyz[1]}) angekommen.")
                        test_done = True

    #print("+++Winkelformatvergleich+++")
    #print("Angle(): " + anki_vector.util.Angle(degrees=0))
    #print("degrees(): " + degrees(environment.enemy.rotation))
    #print("Angle(rotation): " + anki_vector.util.Angle(degrees=environment.enemy.rotation))


def test():

    environment = Environment()
    robot = anki_vector.Robot(serial = SERIAL)
    robot.connect()
    robot.behavior.set_eye_color(0.05, 1.0) #Augenfarbe orange

    with behavior.ReserveBehaviorControl(serial= SERIAL):

        test_general(robot, environment)
        #test_proximity(robot, environment)
        #test_custom_object(robot, environment)

    robot.disconnect()


   
if __name__ == "__main__":
    test()

