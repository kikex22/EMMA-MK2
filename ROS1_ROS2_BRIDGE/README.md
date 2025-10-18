This node acts as a ROS2 ↔ ROS1 data bridge, allowing a mixed system to share camera streams and AI detection results across both environments.
It converts and synchronizes compressed image topics and bounding box detections, letting older ROS1 tools (like RViz or Gazebo plugins) work seamlessly with modern ROS2-based perception nodes.
