This node acts as a dynamic 3D visualization bridge between Gazebo and RViz.
It listens to Gazebo’s model states, transforms their positions into the robot’s map frame using TF, and publishes visually aligned 3D mesh and text markers in RViz 
allowing real-time tracking and labeling of simulated objects in the environment.
