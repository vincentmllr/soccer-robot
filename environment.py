import anki_vector, multiprocessing, time
from anki_vector.util import degrees, Pose
from anki_vector import behavior

class Environment():
    """Representation of vectors environment/ the soccer field with all its objects.

    """
    
    def __init__(self):
        self.field_length_x = 2000.0
        self.field_length_y = 1000.0
        self.field_height = 150.0
        self.wall_thickness = 10.0
        self.goal_width = 200.0
        self.goal_height = 100.0
        self.position_start_x = 100.0
        self.position_start_y = 500.0
        self.self = EnvironmentObject("Self", self.position_start_x, self.position_start_y, degrees(0), 0, self)
        self.ball = EnvironmentObject("Ball", (self.field_length_x)/2, self.position_start_y, degrees(0), 0, self)
        self.enemy = EnvironmentObject("Enemy", self.field_length_x-self.position_start_x, self.position_start_y, degrees(0), 0, self)
        self.goal_self = EnvironmentObject("Goal_self", 0, self.position_start_y, degrees(0), 0, self)
        self.goal_enemy = EnvironmentObject("Goal_enemy", self.field_length_x, self.position_start_y, degrees(0), 0, self)
    

class EnvironmentObject():

    def __init__(self, tag, position_x, position_y, rotation, time, environment):
        self.tag = tag
        self.position_x = position_x
        self.position_y = position_y
        self.rotation = rotation
        self.moment = time
        self.environment = environment
        if tag == "enemy":
            environment.enemy = self
        elif tag == "ball":
            environment.ball = self
        elif tag == "goal_self":
            environment.goal_self = self
        elif tag == "goal_enemy":
            environment.goal_enemy = self


def custom_object_test(robot, environment):
    print("+++CustomObject-Test+++")
    #Erstellt die Wände
    wall_left = robot.world.create_custom_fixed_object(
        Pose(x=-environment.position_start_x, y=environment.position_start_y, z=0, angle_z=degrees(0)), 
        x_size_mm=environment.field_length, 
        y_size_mm=environment.wall_thickness, 
        z_size_mm=environment.field_height,
        relative_to_robot=True)
    wall_right = robot.world.create_custom_fixed_object(
        Pose(x=-environment.position_start_x, y=-environment.position_start_y, z=0, angle_z=degrees(0)), 
        x_size_mm=environment.field_length, 
        y_size_mm=environment.wall_thickness, 
        z_size_mm=environment.field_height,
        relative_to_robot=True)
    wall_self = robot.world.create_custom_fixed_object(
        Pose(x=-environment.position_start_x, y=-environment.position_start_y, z=0, angle_z=degrees(90)), 
        x_size_mm=environment.field_width, 
        y_size_mm=environment.wall_thickness, 
        z_size_mm=environment.field_height,
        relative_to_robot=True)
    wall_oponent = robot.world.create_custom_fixed_object(
        Pose(x=-environment.position_start_x, y=environment.field_length-environment.position_start_y, z=0, angle_z=degrees(90)), 
        x_size_mm=environment.field_width, 
        y_size_mm=environment.wall_thickness, 
        z_size_mm=environment.field_height,
        relative_to_robot=True)  
    print("Alle Objekte:")
    for obj in robot.world.all_objects:
        print(obj)  

    
def proximity_test(robot):
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


def test():

    args = anki_vector.util.parse_command_args()

    with anki_vector.Robot(args.serial) as robot:

        robot.behavior.drive_on_charger()

        robot.behavior.drive_off_charger() 
        robot.motors.set_wheel_motors(-100, 100)

        proximity_test(robot)

   
if __name__ == "__main__":
    test()


"""
##NavMap Ansatz

anki_vector.nav_map.NavMapComponent.init_nav_map_feed(0.5)     #Initialisierung

#Test
print("+++Test für NavMap+++")
robot.behavior.drive_off_charger()
robot.motors.set_wheel_motors(-100,100)
latest_nav_map = robot.nav_map.latest_nav_map

content=latest_nav_map.get_content(0.0,100.0)
print(f"Sampling point at 0.0, 100.0 and found content: {content}")
size = latest_nav_map.size
print(f"Size: {size}")
print(f"Center:  {latest_nav_map.center}")

for i in range(1, size):
    for j in range(1,size):
        node=latest_nav_map.get_node(i,j)
        content=latest_nav_map.get_content(i,j)
        node_content = node.content
        print(f"Node: {node} with Content: {content} and Node-Content: {node_content} at {i},{j}.")

#robot.nav_map.NavMapComponent.close_nav_map_feed()     #Terminierung

##Viewer3DComponent

robot.viewer_3d.show()
print("+++Viewer3D-Test:+++")
#Test: Zeichne Punkt in World Origin, Geht ohne freeglut?
def render_function(user_data_queue):
    glBegin(GL_POINTS)
    glVertex3f(0, 0, 0)
    #glEnd()

robot.viewer_3d.add_render_call(render_function)
time.sleep(10)

robot.viewer_3d.close()
"""

