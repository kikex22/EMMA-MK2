import rospy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import sys
import termios
import tty

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def clamp(value, min_value, max_value):
    """Limita el valor entre un mínimo y un máximo."""
    return max(min_value, min(value, max_value))

def main():
    rospy.init_node('arm_keyboard_control')
    pub = rospy.Publisher('/jetauto/arm_controller/command', JointTrajectory, queue_size=1)

    positions = [0.0, -0.83776, 1.16, 1.19380, 0.0]  
    joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5']  

    print("Usa las teclas 1-5 para incrementar el ángulo del joint respectivo.")
    print("Usa las teclas q-w-e-r-t para decrementar el ángulo del joint respectivo.")
    print("Presiona 'z' para poner joint3=1.50 y los demás joints en 0.")
    print("Presiona 's' para salir.")

    step = 0.1

    # Límites de seguridad
 

    rate = rospy.Rate(10)

    while not rospy.is_shutdown():
        key = getch()
        if key == 's':
            print("Saliendo...")
            break
        elif key == '1':
            positions[0] += step
        elif key == 'q':
            positions[0] -= step
        elif key == '2':
            positions[1] += step
        elif key == 'w':
            positions[1] -= step
        elif key == '3':
            positions[2] += step
        elif key == 'e':
            positions[2] -= step
        elif key == '4':
            positions[3] += step
        elif key == 'r':
            positions[3] -= step
        elif key == '5':
            positions[4] += step
        elif key == 't':
            positions[4] -= step
        elif key == 'z':
            positions = [0.0, 0.0, 1.50, 0.0, 0.0]
        else:
            continue

        # Aplicar límites de seguridad
      
        traj = JointTrajectory()
        traj.joint_names = joint_names

        point = JointTrajectoryPoint()
        point.positions = positions
        point.velocities = [0] * len(joint_names)
        point.time_from_start = rospy.Duration(1.0)

        traj.points = [point]

        pub.publish(traj)
        print(f"Posiciones enviadas: {positions}")

        rate.sleep()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass

