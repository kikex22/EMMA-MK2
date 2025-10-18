#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

bridge = CvBridge()

def callback(msg):
    try:
        # Convertir de ROS Image a OpenCV
        cv_image = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        # Rotar 90 grados clockwise
        rotated = cv2.rotate(cv_image, cv2.ROTATE_90_CLOCKWISE)
        # Convertir de vuelta a ROS Image
        rotated_msg = bridge.cv2_to_imgmsg(rotated, encoding='bgr8')
        # Mantener el header original para sincronización y timestamp
        rotated_msg.header = msg.header
        # Publicar la imagen rotada
        pub.publish(rotated_msg)
    except CvBridgeError as e:
        rospy.logerr("CvBridge Error:%s" % e)

if __name__ == '__main__':
    rospy.init_node('image_rotate_node')
    # Publicador de la imagen rotada
    pub = rospy.Publisher('/jetauto/usb_cam/image_rotated', Image, queue_size=1)
    # Suscriptor de la imagen original
    sub = rospy.Subscriber('/jetauto/usb_cam/image_raw', Image, callback)
    rospy.spin()

