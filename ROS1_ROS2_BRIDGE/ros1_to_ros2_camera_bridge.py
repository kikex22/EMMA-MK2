#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from darkhelp_msgs.msg import BoundingBoxes, BoundingBox  # <-- IMPORTANTE
import roslibpy
import numpy as np
import base64
import time
import cv2
import cv_bridge


class Ros1BridgeNode(Node):
    def __init__(self):
        super().__init__('ros1_bridge_node')

        # --- cv_bridge para convertir OpenCV <-> ROS2
        self.bridge = cv_bridge.CvBridge()

        # --- Publicador en ROS2 (Image)
        self.img_pub = self.create_publisher(Image, '/ros2/image_topic', 10)

        # --- Suscripción a bounding boxes en ROS2
        self.bb_sub = self.create_subscription(
            BoundingBoxes,
            '/darkhelp/bounding_boxes',
            self.bounding_boxes_callback,
            10
        )

        # --- Conexión a ROS1 vía rosbridge
        self.client = roslibpy.Ros(host='192.168.255.135', port=9090)
        self.client.run()
        self.get_logger().info(" Conectado a ROS1 vía rosbridge")

        # --- Publicador ROS1 para imagen comprimida
        self.ros1_pub_img = roslibpy.Topic(
            self.client,
            '/darkhelp/image_out',
            'sensor_msgs/CompressedImage'
        )
        self.ros1_pub_img.advertise()

        # --- Publicador ROS1 para bounding boxes
        self.ros1_pub_boxes = roslibpy.Topic(
            self.client,
            '/darkhelp/bounding_boxes',
            'darkhelp_msgs/BoundingBoxes'
        )
        self.ros1_pub_boxes.advertise()

        # --- Suscripción al tópico comprimido de ROS1
        self.listener = roslibpy.Topic(
            self.client,
            '/jetauto/usb_cam/image_raw/compressed',
            'sensor_msgs/CompressedImage'
        )
        self.listener.subscribe(self.image_callback)
        self.get_logger().info("Suscrito a /jetauto/usb_cam/image_raw/compressed")

        # Contadores para FPS
        self.frame_count = 0
        self.last_time = time.time()

    def image_callback(self, msg):
        try:
            # Decodificar JPEG de ROS1
            if isinstance(msg['data'], str):
                decoded_bytes = base64.b64decode(msg['data'])
            else:
                decoded_bytes = np.array(msg['data'], dtype=np.uint8).tobytes()

            # Reconstruir imagen OpenCV
            cv_img = cv2.imdecode(np.frombuffer(decoded_bytes, np.uint8), cv2.IMREAD_COLOR)
            if cv_img is None:
                raise ValueError("No se pudo decodificar la imagen comprimida")

            # --- Publicar en ROS2 ---
            ros2_msg = self.bridge.cv2_to_imgmsg(cv_img, encoding='bgr8')
            ros2_msg.header.frame_id = "camera_link"
            ros2_msg.header.stamp = self.get_clock().now().to_msg()
            self.img_pub.publish(ros2_msg)

            # --- Reenviar a ROS1 como CompressedImage ---
            ros1_msg = {
                'header': msg['header'],
                'format': 'jpeg',
                'data': base64.b64encode(decoded_bytes).decode('utf-8')
            }
            self.ros1_pub_img.publish(ros1_msg)

            # --- FPS ---
            self.frame_count += 1
            now = time.time()
            elapsed = now - self.last_time
            if elapsed >= 1.0:
                fps = self.frame_count / elapsed
                self.get_logger().info(" FPS: {:.2f}".format(fps))
                self.frame_count = 0
                self.last_time = now

        except Exception as e:
            self.get_logger().error(" Error al procesar la imagen: {}".format(e))

    def bounding_boxes_callback(self, msg):
        try:
            # Convertir BoundingBoxes de ROS2 a diccionario para ROS1
            boxes_list = []
            for box in msg.bounding_boxes:
                boxes_list.append({
                    'name': box.name,
                    'probability': float(box.probability),
                    'x': int(box.x),
                    'y': int(box.y),
                    'width': int(box.width),
                    'height': int(box.height)
                })

            ros1_boxes_msg = {
                'bounding_boxes': boxes_list
            }
            self.ros1_pub_boxes.publish(ros1_boxes_msg)
            self.get_logger().info(" Enviadas {} bounding boxes a ROS1".format(len(boxes_list)))

        except Exception as e:
            self.get_logger().error(" Error al reenviar bounding boxes: {}".format(e))


def main(args=None):
    rclpy.init(args=args)
    node = Ros1BridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.listener.unsubscribe()
        node.ros1_pub_img.unadvertise()
        node.ros1_pub_boxes.unadvertise()
        node.client.terminate()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
