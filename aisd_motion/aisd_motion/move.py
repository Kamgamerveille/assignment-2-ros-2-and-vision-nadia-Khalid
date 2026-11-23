
import rclpy
from rclpy.node import Node
from aisd_msgs.msg import Hand
from geometry_msgs.msg import Twist


class Move(Node):

    def __init__(self):
        super().__init__('move')

        # Subscribe to hand information from the vision node
        self.subscription = self.create_subscription(
            Hand,
            'cmd_hand',
            self.listener_callback,
            10
        )

        # Publish movement commands to Turtlesim
        self.vel_publisher = self.create_publisher(
            Twist,
            'cmd_vel',
            10
        )

        # Stop if hand messages are no longer received
        self.last_hand_time = self.get_clock().now()
        self.create_timer(0.2, self.check_timeout)

    def listener_callback(self, msg):

        self.last_hand_time = self.get_clock().now()

        # Initialize movement speeds
        angle = 0.0
        linear = 0.0

        # Move only when the index finger is raised
        if msg.xpinky == 1.0:

            if msg.xindex > 0.55:
                self.get_logger().info('right')
                angle = -0.5
                linear = 0.5

            elif msg.xindex < 0.45:
                self.get_logger().info('left')
                angle = 0.5
                linear = 0.5

            else:
                self.get_logger().info('forward')
                linear = 0.5

        else:
            self.get_logger().info('stop')

        # Create and publish the movement command
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angle

        self.vel_publisher.publish(twist)

    def check_timeout(self):

        # Stop if no hand message arrives for 0.5 seconds
        elapsed = (
            self.get_clock().now() - self.last_hand_time
        ).nanoseconds / 1e9

        if elapsed > 0.5:
            self.vel_publisher.publish(Twist())


def main(args=None):
    rclpy.init(args=args)

    move = Move()

    try:
        rclpy.spin(move)
    except KeyboardInterrupt:
        pass
    finally:
        move.vel_publisher.publish(Twist())
        move.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

