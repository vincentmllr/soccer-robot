import anki_vector, multiprocessing, time
from anki_vector.util import degrees, Pose
from anki_vector import behavior
"""
class Map():
    
    def __init__(self):
        self.robot = MapObject()
        self.ball = MapObject()
        self.enemy = MapObject()
        self.goal_self = MapObject()
        self.goal_enemy = MapObject()

class MapObject():

    def __init__(tag, position_x, position_y, time, map):
        self.tag = tag
        self.position_x = position_x
        self.position_y = position_y
        self.moment = time
        self.map = map
        if tag == "enemy":
            map.enemy = self
        elif tag == "ball":
            map.ball = self
        elif tag == "goal_self":
            map.goal_self
        #[...]
"""
#Feldparameter
field_length = 2000
field_width = 1000
field_height = 150
wall_thickness = 10

#Torparameter
goal_width = 200
goal_height = 100

#Startposition
position_start_x = 100
position_start_y = 500

IP_ADDRESS = '192.168.0.136'
SERIAL = '008014c1'


def main():

    with anki_vector.Robot(enable_nav_map_feed=True) as robot:

        robot.behavior.drive_off_charger()      




    #with anki_vector.Robot(enable_nav_map_feed=True) as robot: #navmap für navmap und 3DViewer, 3dviewer für 3d viewer
    #, show_3d_viewer=True
    ##NavMap Ansatz
    #anki_vector.nav_map.NavMapComponent.init_nav_map_feed(0.5)     #Initialisierung
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

    # for i in range(1, size):
    #    for j in range(1,size):
    #        node=latest_nav_map.get_node(float(i),float(j))
    #        content=latest_nav_map.get_content(float(i),float(j))
    #        node_content = node.content
    #        print( "Blabla")#f"Node: {node} with Content: {content} and Node-Content: {node_content} at {i},{j}.")
    
    #robot.nav_map.NavMapComponent.close_nav_map_feed()     #Terminierung
"""
    ##Vision
    robot.vision.enable_custom_object_detection #Können fixed objects betrachtet werden?

    ##World-Ansatz

    #Erstellt die Wände
    wall_left = robot.world.create_custom_fixed_object(
        Pose(x=-position_start_x, y=position_start_y, z=0, angle_z=degrees(0)), 
        x_size_mm=field_length, 
        y_size_mm=wall_thickness, 
        z_size_mm=field_height,
        relative_to_robot=True)
    wall_right = robot.world.create_custom_fixed_object(
        Pose(x=-position_start_x, y=-position_start_y, z=0, angle_z=degrees(0)), 
        x_size_mm=field_length, 
        y_size_mm=wall_thickness, 
        z_size_mm=field_height,
        relative_to_robot=True)
    wall_self = robot.world.create_custom_fixed_object(
        Pose(x=-position_start_x, y=-position_start_y, z=0, angle_z=degrees(90)), 
        x_size_mm=field_width, 
        y_size_mm=wall_thickness, 
        z_size_mm=field_height,
        relative_to_robot=True)
    wall_oponent = robot.world.create_custom_fixed_object(
        Pose(x=-position_start_x, y=field_length-position_start_y, z=0, angle_z=degrees(90)), 
        x_size_mm=field_width, 
        y_size_mm=wall_thickness, 
        z_size_mm=field_height,
        relative_to_robot=True)

    #Gibt Alle Objekte in der Welt aus
    print("+++World-Test:+++")
    for obj in robot.world.all_objects:
        print(obj)


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
    
    ##OpenGL Ansatz (freeglut Defekt -> Funktioniert nicht)
    
    ctx = multiprocessing.get_context('spawn')
    close_event = ctx.Event()
    input_intent_queue = ctx.Queue(maxsize=10)
    nav_map_queue = ctx.Queue(maxsize=10)
    world_frame_queue = ctx.Queue(maxsize=10)
    extra_render_function_queue = ctx.Queue(maxsize=1)
    user_data_queue = ctx.Queue()
    process = ctx.Process(target=opengl.main,
        args=(close_event,
            input_intent_queue,
            nav_map_queue,
            world_frame_queue,
            extra_render_function_queue,
            user_data_queue),
        daemon=True)
    process.start()
    
    
    ##Proximity
    print("+++Proximity-Test:+++")
    proximity_data=robot.proximity.last_sensor_reading
    if proximity_data is not None:
        print('Proximity distance: {0}' .format(proximity_data))
        print(proximity_data.distance)
        print(proximity_data.found_object)
        print(proximity_data.is_lift_in_fov)
        print(proximity_data.signal_quality)
        print(proximity_data.unobstructed)


    ##Touch
    #Beim Zurückstellen so berühren,
    #dass man unterschiedliche Modi einstellt (nicht Sinn der Sache)

    #Roboter legen selbst fest, welches Tor wem gehört und wechseln Seite automatisch

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

if __name__ == "__main__":
    main()