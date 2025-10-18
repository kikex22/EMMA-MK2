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

def main():
    rospy.init_node('gripper_keyboard_control')
    pub = rospy.Publisher('/jetauto/gripper_controller/command', JointTrajectory, queue_size=1)
    
    position = 0.0
    joint_names = ['r_joint']
    
    print("Presiona 'o' para abrir el gripper.")
    print("Presiona 'p' para cerrar el gripper.")
    print("Presiona 'z' para abrir a 0.5 radianes de golpe.")
    print("Presiona 's' para salir.")

    step = 0.05
    rate = rospy.Rate(10)

    while not rospy.is_shutdown():
        tecla = getch()
        if tecla == 's':
            print("Saliendo...")
            break
        elif tecla == 'o':
            position += step
        elif tecla == 'p':
            position -= step
        elif tecla == 'z':
            position = 0.5
        else:
            continue

        # Limitar posición
        position = max(0.0, min(2.0, position))

        # Crear mensaje de trayectoria
        traj = JointTrajectory()
        traj.joint_names = joint_names
        point = JointTrajectoryPoint()
        point.positions = [position]
        point.time_from_start = rospy.Duration(0.5)  # medio segundo para llegar
        traj.points = [point]

        # Publicar
        pub.publish(traj)
        print(f"Posición enviada al gripper: {position:.2f}")
        rate.sleep()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
