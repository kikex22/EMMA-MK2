#!/usr/bin/env python
import rospy
from gazebo_ros_link_attacher.srv import Attach, AttachRequest
from gazebo_msgs.msg import ContactsState
import sys
import termios
import tty
import math

# Umbral de fuerza para auto-detach (ajústalo según tu cubo y simulación)
SAFE_FORCE_THRESHOLD = 50.0  # Newtons

# Estado de contacto actual
contact_forces = {}

# Función para leer una sola tecla
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# Función para attachar un objeto a un link
def attach(gripper_model, gripper_link, object_model, object_link):
    rospy.wait_for_service('/link_attacher_node/attach')
    try:
        attach_srv = rospy.ServiceProxy('/link_attacher_node/attach', Attach)
        req = AttachRequest()
        req.model_name_1 = gripper_model
        req.link_name_1 = gripper_link
        req.model_name_2 = object_model
        req.link_name_2 = object_link
        if hasattr(req, "disable_collisions"):
            req.disable_collisions = True
        resp = attach_srv(req)
        if resp.ok:
            rospy.loginfo(f"{gripper_link} attachado correctamente con {object_model}")
        else:
            rospy.logerr(f"No se pudo attachar {gripper_link}")
    except rospy.ServiceException as e:
        rospy.logerr("Error en attach: %s" % e)

# Función para desattachar un objeto de un link
def detach(gripper_model, gripper_link, object_model, object_link):
    rospy.wait_for_service('/link_attacher_node/detach')
    try:
        detach_srv = rospy.ServiceProxy('/link_attacher_node/detach', Attach)
        req = AttachRequest()
        req.model_name_1 = gripper_model
        req.link_name_1 = gripper_link
        req.model_name_2 = object_model
        req.link_name_2 = object_link
        resp = detach_srv(req)
        if resp.ok:
            rospy.loginfo(f"{gripper_link} desattachado correctamente de {object_model}")
        else:
            rospy.logerr(f"No se pudo desattachar {gripper_link}")
    except rospy.ServiceException as e:
        rospy.logerr("Error en detach: %s" % e)

# Callback para recibir las fuerzas de contacto
def contact_callback(msg):
    global contact_forces
    for state in msg.states:
        # Filtrar solo las colisiones que involucren el gripper y el objeto
        if ("r_out_link" in state.collision1_name or "l_out_link" in state.collision1_name) and \
           ("wood_cube_5cm" in state.collision2_name):
            key = f"{state.collision1_name}->{state.collision2_name}"
            total_force = math.sqrt(
                state.total_wrench.force.x**2 +
                state.total_wrench.force.y**2 +
                state.total_wrench.force.z**2
            )
            contact_forces[key] = total_force

# Función para chequear fuerzas y auto-detach si se excede
def check_forces(gripper_model, gripper_link, object_model, object_link):
    for key, force in contact_forces.items():
        if force > SAFE_FORCE_THRESHOLD:
            rospy.logwarn(f"Fuerza {force:.3f} N detectada en {key}, desattachando...")
            detach(gripper_model, gripper_link, object_model, object_link)
            return True
    return False

if __name__ == "__main__":
    rospy.init_node("attach_trash_bin_safe")

    gripper_model = "jetauto"
    object_model = "can_pepsi_0"
    object_link = "link_0"

    # Suscripción al topic de contactos de Gazebo
    rospy.Subscriber("/gazebo/contact_states", ContactsState, contact_callback)

    rospy.loginfo("Presiona 'a' para agarrar, 't' para soltar, 'q' para salir")

    while not rospy.is_shutdown():
        key = getch()
        if key == 'a':
            attach(gripper_model, "r_out_link", object_model, object_link)
            attach(gripper_model, "l_out_link", object_model, object_link)
        elif key == 't':
            detach(gripper_model, "r_out_link", object_model, object_link)
            detach(gripper_model, "l_out_link", object_model, object_link)
        elif key == 'q':
            rospy.loginfo("Saliendo...")
            break

        # Auto-detach si fuerza supera el umbral
        check_forces(gripper_model, "r_out_link", object_model, object_link)
        check_forces(gripper_model, "l_out_link", object_model, object_link)

