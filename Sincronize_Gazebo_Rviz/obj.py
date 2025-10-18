#!/usr/bin/env python
import rospy
import tf2_ros
import tf2_geometry_msgs
import tf
from visualization_msgs.msg import Marker
from geometry_msgs.msg import PoseStamped
from gazebo_msgs.msg import ModelStates
import math

# Lista de objetos a mostrar y sus offsets
objetos_mesh = {
    'can_pepsi': 'package://objects/gazebo_models/can_pepsi/meshes/body.dae',
    'can_coke':  'package://objects/gazebo_models/can_coke/meshes/body.dae',
    'can_fanta': 'package://objects/gazebo_models/can_fanta/meshes/body.dae',
    'can_sprite':'package://objects/gazebo_models/can_sprite/meshes/body.dae',
    'tea_table': 'package://jetauto_gazebo/meshes/tea_table.dae'
}

# Diccionario para guardar ultima pose conocida de cada objeto
objetos_pose = {name: None for name in objetos_mesh.keys()}

# Offsets manuales para alinear mejor los objetos en el mapa
offsets = {
    'can_pepsi': (-2.2, 0.36, 0.0),
    'can_coke':  (-1, 0.45, 0.0),
    'can_fanta': (-2.2, 0.46, 0.0),
    'can_sprite':(-1.96, 0.367, 0.0),
    'tea_table': (-1.64, 0.0, 0.0)
}

# Publisher de markers
pub = None

# TF buffer y listener
tf_buffer = None
tf_listener = None

def model_states_callback(msg):
    for name, pose in zip(msg.name, msg.pose):
        if name in objetos_mesh:
            objetos_pose[name] = pose

def publicar_markers():
    global pub, tf_buffer
    id_count = 0
    for name, pose in objetos_pose.items():
        if pose is None:
            continue

        # Creamos pose en frame 'world'
        pose_world = PoseStamped()
        pose_world.header.frame_id = "jetauto/world"
        pose_world.header.stamp = rospy.Time.now()
        pose_world.pose.position.x = pose.position.x + offsets[name][0]
        pose_world.pose.position.y = pose.position.y + offsets[name][1]
        pose_world.pose.position.z = pose.position.z + offsets[name][2]
        pose_world.pose.orientation = pose.orientation

        # Ajuste opcional de rotacion en yaw
        roll, pitch, yaw = tf.transformations.euler_from_quaternion([
            pose_world.pose.orientation.x,
            pose_world.pose.orientation.y,
            pose_world.pose.orientation.z,
            pose_world.pose.orientation.w
        ])
        yaw += -0.2  # ajuste manual si hace falta
        q = tf.transformations.quaternion_from_euler(roll, pitch, yaw)
        pose_world.pose.orientation.x = q[0]
        pose_world.pose.orientation.y = q[1]
        pose_world.pose.orientation.z = q[2]
        pose_world.pose.orientation.w = q[3]

        try:
            # Transformamos al frame 'jetauto/map'
            pose_map = tf_buffer.transform(pose_world, "jetauto/map", rospy.Duration(1.0))
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException):
            rospy.logwarn("No se pudo transformar %s" % name)
            continue

        # --- Imprimir en terminal ---
        rospy.loginfo("{} -> x: {:.3f}, y: {:.3f}, z: {:.3f}".format(
            name,
            pose_map.pose.position.x,
            pose_map.pose.position.y,
            pose_map.pose.position.z
        ))

        # Marker del mesh
        marker = Marker()
        marker.header.frame_id = "jetauto/map"
        marker.header.stamp = rospy.Time.now()
        marker.ns = "objetos_mesh"
        marker.id = id_count
        marker.type = Marker.MESH_RESOURCE
        marker.mesh_resource = objetos_mesh[name]
        marker.action = Marker.ADD
        marker.pose.position = pose_map.pose.position
        marker.pose.orientation = pose_map.pose.orientation
        marker.scale.x = 1.0
        marker.scale.y = 1.0
        marker.scale.z = 1.0
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        marker.color.a = 1.0
        marker.mesh_use_embedded_materials = True
        pub.publish(marker)

        # Marker de texto en RViz
        text_marker = Marker()
        text_marker.header.frame_id = "jetauto/map"
        text_marker.header.stamp = rospy.Time.now()
        text_marker.ns = "objetos_text"
        text_marker.id = id_count + 1000
        text_marker.type = Marker.TEXT_VIEW_FACING
        text_marker.action = Marker.ADD
        text_marker.pose.position.x = pose_map.pose.position.x
        text_marker.pose.position.y = pose_map.pose.position.y
        text_marker.pose.position.z = pose_map.pose.position.z + 0.2
        text_marker.pose.orientation.x = 0
        text_marker.pose.orientation.y = 0
        text_marker.pose.orientation.z = 0
        text_marker.pose.orientation.w = 1
        text_marker.scale.z = 0.1
        text_marker.color.r = 1.0
        text_marker.color.g = 1.0
        text_marker.color.b = 0.0
        text_marker.color.a = 1.0
        text_marker.text = "{}\n({:.2f}, {:.2f}, {:.2f})".format(
            name,
            pose_map.pose.position.x,
            pose_map.pose.position.y,
            pose_map.pose.position.z
        )
        pub.publish(text_marker)

        id_count += 1

if __name__ == "__main__":
    rospy.init_node('rviz_mesh_objects_dynamic')
    pub = rospy.Publisher('objetos_mesh_marker', Marker, queue_size=10)

    # Setup TF
    tf_buffer = tf2_ros.Buffer()
    tf_listener = tf2_ros.TransformListener(tf_buffer)

    rospy.Subscriber('/gazebo/model_states', ModelStates, model_states_callback)

    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        publicar_markers()
        rate.sleep()

