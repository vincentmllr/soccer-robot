import anki_vector
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


with anki_vector.Robot() as robot:

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

    #Initialisierung
    anki_vector.nav_map.NavMapComponent.init_nav_map_feed(0.5)

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
    
    #Terminierung
    #robot.nav_map.NavMapComponent.close_nav_map_feed()

    #OpenGL Ansatz

    #Proximity

    #Touch

    #Vision

    #Viewer3DComponent

