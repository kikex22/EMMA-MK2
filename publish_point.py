#!/usr/bin/env python
# encoding: utf-8
import rospy
import numpy as np
from std_srvs.srv import Empty, EmptyResponse
from move_base_msgs.msg import MoveBaseActionResult, MoveBaseActionGoal
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import PointStamped, PoseStamped
import actionlib_msgs.msg
import uuid

goal_count = 0
try_again = True
goal_reached_count = 0
haved_clicked = False
add_more_point = False
enable_navigation = True
markerArray = MarkerArray()
loop_enabled = False

def make_move_base_goal(pose_stamped):
    goal = MoveBaseActionGoal()
    goal.header.stamp = rospy.Time.now()
    goal.header.frame_id = pose_stamped.header.frame_id
    goal.goal_id.stamp = rospy.Time.now()
    goal.goal_id.id = str(uuid.uuid4())
    goal.goal.target_pose = pose_stamped
    return goal

def status_callback(msg):
    global try_again, goal_reached_count, add_more_point, enable_navigation, loop_enabled

    if haved_clicked:
        try:
            if msg.status.status == 3 or msg.status.status == 4:
                if msg.status.status == 3:
                    if goal_reached_count < goal_count:
                        goal_reached_count += 1
                        print('******number %s goal reached******' % goal_reached_count)

                if goal_reached_count < goal_count:
                    if enable_navigation:
                        rospy.sleep(0.1)
                        pose = PoseStamped()
                        pose.header.frame_id = map_frame
                        pose.header.stamp = rospy.Time.now()
                        pose.pose.position.x = markerArray.markers[goal_reached_count].pose.position.x
                        pose.pose.position.y = markerArray.markers[goal_reached_count].pose.position.y
                        pose.pose.orientation.z = 1
                        goal_msg = make_move_base_goal(pose)
                        goal_pub.publish(goal_msg)
                        print('******send number %s goal******' % (goal_reached_count + 1))

                elif goal_reached_count == goal_count:
                    print('******all points reached******')
                    add_more_point = True
                    if loop_enabled:
                        rospy.sleep(0.5)
                        goal_reached_count = 0
                        pose = PoseStamped()
                        pose.header.frame_id = map_frame
                        pose.header.stamp = rospy.Time.now()
                        pose.pose.position.x = markerArray.markers[goal_reached_count].pose.position.x
                        pose.pose.position.y = markerArray.markers[goal_reached_count].pose.position.y
                        pose.pose.orientation.z = 1
                        goal_msg = make_move_base_goal(pose)
                        goal_pub.publish(goal_msg)
                        print('******looping to point 1******')

                try_again = True

            else:
                print('******Goal cannot be reached, error:', msg.status.status, 'trying again******')
                if try_again:
                    pose = PoseStamped()
                    pose.header.frame_id = map_frame
                    pose.header.stamp = rospy.Time.now()
                    pose.pose.position.x = markerArray.markers[goal_reached_count].pose.position.x
                    pose.pose.position.y = markerArray.markers[goal_reached_count].pose.position.y
                    pose.pose.orientation.z = 1
                    goal_msg = make_move_base_goal(pose)
                    goal_pub.publish(goal_msg)
                    try_again = False
                elif goal_reached_count < goal_count:
                    goal_reached_count += 1
                    pose = PoseStamped()
                    pose.header.frame_id = map_frame
                    pose.header.stamp = rospy.Time.now()
                    pose.pose.position.x = markerArray.markers[goal_reached_count].pose.position.x
                    pose.pose.position.y = markerArray.markers[goal_reached_count].pose.position.y
                    pose.pose.orientation.z = 1
                    goal_msg = make_move_base_goal(pose)
                    goal_pub.publish(goal_msg)
        except BaseException as e:
            print(e)

def click_callback(msg):
    global add_more_point, markerArray
    global goal_count, haved_clicked, loop_enabled

    goal_count += 1
    print('******add number %s goal******' % goal_count)

    marker = Marker()
    marker.header.frame_id = map_frame
    marker.type = marker.TEXT_VIEW_FACING
    marker.action = marker.ADD
    marker.scale.x = 0.5
    marker.scale.y = 0.5
    marker.scale.z = 0.5
    color = list(np.random.choice(range(256), size=3))
    marker.color.a = 1
    marker.color.r = color[0]/255.0
    marker.color.g = color[1]/255.0
    marker.color.b = color[2]/255.0
    marker.pose.position.x = msg.point.x
    marker.pose.position.y = msg.point.y
    marker.pose.position.z = msg.point.z
    marker.pose.orientation.w = 1
    marker.text = str(goal_count)

    markerArray.markers.append(marker)
    for i, m in enumerate(markerArray.markers):
        m.id = i
    mark_pub.publish(markerArray)

    if enable_navigation:
        if goal_count == 1:
            pose = PoseStamped()
            pose.header.frame_id = map_frame
            pose.header.stamp = rospy.Time.now()
            pose.pose.position.x = msg.point.x
            pose.pose.position.y = msg.point.y
            pose.pose.orientation.z = 1
            goal_msg = make_move_base_goal(pose)
            goal_pub.publish(goal_msg)
            print('******send number %s goal******' % goal_count)
        elif add_more_point:
            add_more_point = False
            move = MoveBaseActionResult()
            move.status.status = 4
            move.header.stamp = rospy.Time.now()
            print('******add more point******')
            goal_status_pub.publish(move)

    if goal_count == 10:
        loop_enabled = True
        print('******LOOP MODE ENABLED AFTER 10 GOALS******')

    haved_clicked = True

def start_navigation_srv_callback(msg):
    global enable_navigation
    print('******start navigation******')
    enable_navigation = True
    move = MoveBaseActionResult()
    move.status.status = 4
    move.header.stamp = rospy.Time.now()
    goal_status_pub.publish(move)
    return EmptyResponse()

def stop_navigation_srv_callback(msg):
    global enable_navigation
    print('******stop navigation******')
    enable_navigation = False
    move = MoveBaseActionResult()
    move.status.status = 4
    move.header.stamp = rospy.Time.now()
    goal_status_pub.publish(move)
    return EmptyResponse()

def clear_goals_srv_callback(msg):
    global markerArray, goal_count
    print('******clear goals******')
    goal_count = 0
    markerArray = MarkerArray()
    marker_Array = MarkerArray()
    marker = Marker()
    marker.header.frame_id = map_frame
    marker.action = Marker.DELETEALL
    marker_Array.markers.append(marker)
    mark_pub.publish(marker_Array)
    return EmptyResponse()

if __name__ == '__main__':
    rospy.init_node('publish_point_node')

    map_frame = rospy.get_param('~map_frame', 'map')
    enable_navigation = rospy.get_param('~enable_navigation', True)
    clicked_point = rospy.get_param('~clicked_point', '/clicked_point')
    click_sub = rospy.Subscriber(clicked_point, PointStamped, click_callback)

    start_navigation_srv = rospy.get_param('~start_navigation', '/start_navigation')
    stop_navigation_srv = rospy.get_param('~stop_navigation', '/stop_navigation')
    clear_goals_srv = rospy.get_param('~clear_goals', '/clear_goals')

    rospy.Service(start_navigation_srv, Empty, start_navigation_srv_callback)
    rospy.Service(stop_navigation_srv, Empty, stop_navigation_srv_callback)
    rospy.Service(clear_goals_srv, Empty, clear_goals_srv_callback)

    mark_pub = rospy.Publisher('path_point', MarkerArray, queue_size=100)
    goal_pub = rospy.Publisher('/jetauto/move_base/goal', MoveBaseActionGoal, queue_size=1)

    move_base_result = rospy.get_param('~move_base_result', '/move_base/result')
    goal_status_sub = rospy.Subscriber(move_base_result, MoveBaseActionResult, status_callback)
    goal_status_pub = rospy.Publisher(move_base_result, MoveBaseActionResult, queue_size=1)

    rospy.spin()
