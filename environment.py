import anki_vector, multiprocessing, time
from anki_vector.util import degrees, Pose

#Feldparameter
field_length = 2000
field_width = 1000
field_height = 150
wall_thickness = 10

#Torparameter
goal_width = 200
goal_height = 100

#Startposition
start_x = 10
start_y = 50


with anki_vector.Robot(enable_nav_map_feed=True, show_3d_viewer=True) as robot: #navmap für navmap und 3DViewer, 3dviewer für 3d viewer

    ##World-Ansatz

    #Erstellt die Wände
    wall_left = robot.world.create_custom_fixed_object(
        Pose(x=-start_x, y=start_y, z=0, angle_z=degrees(0)), 
        x_size_mm=field_length, 
        y_size_mm=wall_thickness, 
        z_size_mm=field_height,
        relative_to_robot=True)
    wall_right = robot.world.create_custom_fixed_object(
        Pose(x=-start_x, y=-start_y, z=0, angle_z=degrees(0)), 
        x_size_mm=field_length, 
        y_size_mm=wall_thickness, 
        z_size_mm=field_height,
        relative_to_robot=True)
    wall_self = robot.world.create_custom_fixed_object(
        Pose(x=-start_x, y=-start_y, z=0, angle_z=degrees(90)), 
        x_size_mm=field_width, 
        y_size_mm=wall_thickness, 
        z_size_mm=field_height,
        relative_to_robot=True)
    wall_oponent = robot.world.create_custom_fixed_object(
        Pose(x=-start_x, y=field_length-start_y, z=0, angle_z=degrees(90)), 
        x_size_mm=field_width, 
        y_size_mm=wall_thickness, 
        z_size_mm=field_height,
        relative_to_robot=True)

    #Gibt Alle Objekte in der Welt aus
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
    """
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
    """

    ##Proximity

    ##Touch

    ##Vision

    ##Viewer3DComponent

    robot.viewer_3d.show()
    #Test: Zeichne Punkt in World Origin, Geht ohne freeglut?
    def render_function(user_data_queue):
        glBegin(GL_POINTS)
        glVertex3f(0, 0, 0)
        glEnd()

    robot.viewer_3d.add_render_call(render_function)
    time.sleep(10)

    robot.viewer_3d.close()

