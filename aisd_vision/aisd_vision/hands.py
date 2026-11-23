
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import mediapipe as mp

from aisd_msgs.msg import Hand

mp_hands = mp.solutions.hands


class Hands(Node):

    def __init__(self):
        super().__init__('hands')

        # Convert ROS 2 images into OpenCV images
        self.br = CvBridge()

        # Subscribe to the camera images
        self.subscription = self.create_subscription(
            Image,
            'video_frames',
            self.listener_callback,
            10
        )

        # Publish detected hand coordinates
        self.hand_publisher = self.create_publisher(
            Hand, 'cmd_hand', 10
        )

        # Initialize the MediaPipe hand detector
        self.detector = mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def listener_callback(self, msg):

        # Convert the ROS image message into an OpenCV image
        image = self.br.imgmsg_to_cv2(msg)

        # MediaPipe landmark numbers
        PINKY_FINGER_TIP = 20
        INDEX_FINGER_TIP = 8

        # Convert the image from BGR to RGB for MediaPipe
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect hands and their landmarks
        results = self.detector.process(image)

        if results.multi_hand_landmarks:

            # Use the first detected hand
            landmarks = results.multi_hand_landmarks[0].landmark

            # Create a custom Hand message
            hand_msg = Hand()

            # Get the horizontal position of the index finger
            hand_msg.xindex = landmarks[8].x

            # Check if the index finger is raised
            hand_msg.xpinky = 1.0 if landmarks[8].y < landmarks[6].y else 0.0

            # Publish coordinates when a subscriber is connected
            if self.hand_publisher.get_subscription_count() > 0:
                self.hand_publisher.publish(hand_msg)
            else:
                self.get_logger().info('waiting for subscriber')

    def destroy_node(self):
        # Release MediaPipe resources
        self.detector.close()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    hands = Hands()

    try:
        rclpy.spin(hands)
    except KeyboardInterrupt:
        pass
    finally:
        hands.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
