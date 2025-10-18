This script creates a ROS node that receives camera images, rotates them 90° clockwise, and republishes the rotated images.
The script acts as a real-time image rotation node in ROS:
it listens to a camera feed, rotates each frame 90° clockwise, and republishes the corrected image stream for use by other nodes (e.g., vision processing or display modules).
