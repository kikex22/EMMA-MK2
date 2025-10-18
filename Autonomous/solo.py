#!/usr/bin/env python
import rospy
from geometry_msgs.msg import Twist
from darkhelp_ros.msg import BoundingBoxes
from std_msgs.msg import Float64
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import time


class ObjectFollower:
    def __init__(self):
        rospy.init_node('object_follower', anonymous=True)
        
        # Publisher para mover el robot base
        self.cmd_pub = rospy.Publisher('/jetauto/jetauto_controller/cmd_vel', Twist, queue_size=1)
        
        # Publishers para el brazo y el gripper
        self.arm_pub = rospy.Publisher('/jetauto/arm_controller/command', JointTrajectory, queue_size=1)
        self.grip_pub = rospy.Publisher('/r_gripper_controller/command', Float64, queue_size=1)
        
        # Suscriptor al bounding box del objeto detectado
        rospy.Subscriber('/darkhelp/bounding_boxes', BoundingBoxes, self.callback)
        
        # Parametros
        self.image_width = 640         # Ancho de la imagen de la cámara
        self.center_threshold = 50     # Margen de tolerancia en píxeles para estar centrado
        self.forward_speed = 0.15      # Velocidad lineal al avanzar
        self.turn_speed = 0.25         # Velocidad angular para girar
        self.stop_distance = 180       # Ancho del bounding box para detenerse 

        rospy.loginfo("Object Follower listo.")
        rospy.spin()


    def callback(self, data):
        if len(data.bounding_boxes) == 0:
            self.stop_robot()
            return

        # Tomar el primer objeto detectado
        box = data.bounding_boxes[0]
        x_center = box.x + (box.width / 2.0)
        error = x_center - (self.image_width / 2.0)

        cmd = Twist()

        # Centrado horizontal
        if abs(error) < self.center_threshold:
          
            if box.width < self.stop_distance:
                cmd.linear.x = self.forward_speed
                cmd.angular.z = 0.0
                rospy.loginfo("Objeto centrado  Avanzando hacia él...")
            else:
                self.stop_robot()
                rospy.loginfo("Objeto cerca - iniciando movimiento de brazo y gripper.")
                self.move_arm_and_gripper()
        elif error > 0:
            cmd.linear.x = 0.0
            cmd.angular.z = -self.turn_speed
            rospy.loginfo("Objeto a la derecha  girando derecha...")
        else:
            cmd.linear.x = 0.0
            cmd.angular.z = self.turn_speed
            rospy.loginfo("Objeto a la izquierda  girando izquierda...")

        self.cmd_pub.publish(cmd)


    def stop_robot(self):
        cmd = Twist()
        self.cmd_pub.publish(cmd)
        rospy.loginfo("Robot detenido.")


    def move_arm_and_gripper(self):
        # Mover brazo a posición de agarre
        traj = JointTrajectory()
        traj.joint_names = ['joint1', 'joint2', 'joint3']
        point = JointTrajectoryPoint()
        # Aproximadamente joint1=0°, joint2=20°, joint3=72° (en radianes)
        point.positions = [0.0, 0.35, 1.25]
        point.time_from_start = rospy.Duration(2.0)
        traj.points.append(point)

        self.arm_pub.publish(traj)
        rospy.loginfo("Moviendo brazo a posición de agarre...")
        rospy.sleep(2.5)

        # Abrir completamente el gripper
        self.grip_pub.publish(Float64(0.08))  # abre al máximo
        rospy.loginfo("Gripper completamente abierto.")
        rospy.sleep(1.5)

       
        # subprocess.call(["rosservice", "call", "/link_attacher_node/attach", ...])

        rospy.loginfo("Listo para hacer attach del objeto.")


if __name__ == '__main__':
    try:
        ObjectFollower()
    except rospy.ROSInterruptException:
        pass
