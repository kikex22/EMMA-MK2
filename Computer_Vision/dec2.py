#!/usr/bin/env python
import rospy
from sensor_msgs.msg import CompressedImage, Image
from darkhelp_ros.msg import BoundingBoxes
import cv2
from cv_bridge import CvBridge
import numpy as np
import time

bridge = CvBridge()
last_boxes = []      # Ultimas bounding boxes recibidas
last_image = None    # Ultima imagen recibida

pub_decoded = None
pub_boxes = None

# Variables para FPS
prev_time = time.time()
fps = 0.0

def draw_boxes_and_publish():
    global last_image, last_boxes, fps, prev_time
    if last_image is None:
        return

    # Usar la imagen tal como llega (sin rotar)
    cv_img = last_image.copy()

    if last_boxes:
        for box in last_boxes:
            # imprimir valores originales
            print("Box:", box.name, "x:", box.x, "y:", box.y, "width:", box.width, "height:", box.height)

            x1, y1 = int(box.x), int(box.y)
            x2, y2 = x1 + int(box.width), y1 + int(box.height)
            label = "%s (%.2f)" % (box.name, box.probability)
            cv2.rectangle(cv_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(cv_img, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Calcular FPS
    current_time = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / (current_time - prev_time))
    prev_time = current_time
    cv2.putText(cv_img, "FPS: %.2f" % fps, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

    # Publicar imagen con bounding boxes
    ros_image_msg = bridge.cv2_to_imgmsg(cv_img, encoding="bgr8")
    pub_decoded.publish(ros_image_msg)

    # Mostrar en ventana OpenCV
    cv2.imshow("Imagen con Bounding Boxes", cv_img)
    cv2.waitKey(1)

def callback_image(msg):
    global last_image
    try:
        last_image = bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")
        draw_boxes_and_publish()
    except Exception as e:
        rospy.logerr("Error al procesar la imagen: %s" % str(e))

def callback_boxes(msg):
    global last_boxes
    try:
        last_boxes = msg.bounding_boxes
        rospy.loginfo("Recibidas %d bounding boxes" % len(last_boxes))

        # Publicar bounding boxes crudas
        boxes_msg = BoundingBoxes()
        boxes_msg.bounding_boxes = last_boxes
        pub_boxes.publish(boxes_msg)

        # Actualizar imagen con boxes dibujados
        draw_boxes_and_publish()
    except Exception as e:
        rospy.logerr("Error al procesar bounding boxes: %s" % str(e))

if __name__ == "__main__":
    rospy.init_node("ros1_compressed_sub")
    rospy.loginfo("Nodo ROS1 CompressedImage iniciado")

    # Publishers
    pub_decoded = rospy.Publisher("/ros1/image_detected", Image, queue_size=10)
    pub_boxes = rospy.Publisher("/ros1/bounding_boxes", BoundingBoxes, queue_size=10)

    # Subscribers
    rospy.Subscriber("/darkhelp/image_out", CompressedImage, callback_image)
    rospy.Subscriber("/darkhelp/bounding_boxes", BoundingBoxes, callback_boxes)

    try:
        rospy.spin()
    except KeyboardInterrupt:
        rospy.loginfo("Saliendo...")
    finally:
        cv2.destroyAllWindows()
