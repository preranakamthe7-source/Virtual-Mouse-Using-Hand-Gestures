"""
Hand Tracking Module using MediaPipe and OpenCV.
Provides real-time hand detection, 21-landmark tracking, finger state evaluation,
and normalized distance calculations for gesture recognition.
"""

import math
import cv2
import mediapipe as mp

# Support both mp.solutions and direct python.solutions namespace
try:
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    mp_draw_styles = mp.solutions.drawing_styles
except AttributeError:
    try:
        from mediapipe.python.solutions import hands as mp_hands
        from mediapipe.python.solutions import drawing_utils as mp_draw
        from mediapipe.python.solutions import drawing_styles as mp_draw_styles
    except (ImportError, AttributeError):
        mp_hands = None
        mp_draw = None
        mp_draw_styles = None


class HandDetector:
    """
    HandDetector encapsulates Google's MediaPipe Hands model to provide
    streamlined methods for detecting hand landmarks, determining extended
    fingers, and measuring distances between finger tips.
    """

    def __init__(self, mode=False, max_hands=1, detection_con=0.7, track_con=0.6):
        """
        Initialize the HandDetector.

        :param mode: False for streaming video mode, True for static images.
        :param max_hands: Maximum number of hands to detect (1 for mouse control).
        :param detection_con: Minimum detection confidence threshold (0.0 to 1.0).
        :param track_con: Minimum tracking confidence threshold (0.0 to 1.0).
        """
        if mp_hands is None:
            raise ImportError(
                "MediaPipe solutions API is missing.\n"
                "Please run: pip install mediapipe==0.10.14"
            )

        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        # MediaPipe Hands initialization
        self.mp_hands = mp_hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp_draw
        self.mp_draw_styles = mp_draw_styles

        # Landmark tip IDs for the 5 fingers
        self.tip_ids = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        self.pip_ids = [2, 6, 10, 14, 18]  # Corresponding lower joints for reference
        self.results = None

    def find_hands(self, img, draw=True):
        """
        Processes an image frame to detect hands and optionally draws landmarks.

        :param img: BGR image from OpenCV.
        :param draw: Whether to draw landmarks on the image.
        :return: Image with or without landmark drawings.
        """
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks and draw and self.mp_draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    img,
                    hand_lms,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                    self.mp_draw.DrawingSpec(color=(255, 165, 0), thickness=2, circle_radius=2)
                )

        return img

    def find_positions(self, img, hand_no=0):
        """
        Extracts pixel coordinates of all 21 landmarks for a specific hand.

        :param img: Frame image to scale normalized coordinates.
        :param hand_no: Index of hand (default 0).
        :return: (lm_list, bbox) where lm_list contains [id, x, y] and bbox is (xmin, ymin, xmax, ymax).
        """
        lm_list = []
        bbox = (0, 0, 0, 0)

        if self.results and self.results.multi_hand_landmarks:
            if hand_no < len(self.results.multi_hand_landmarks):
                my_hand = self.results.multi_hand_landmarks[hand_no]
                h, w, _ = img.shape
                x_coords = []
                y_coords = []

                for lm_id, lm in enumerate(my_hand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    x_coords.append(cx)
                    y_coords.append(cy)
                    lm_list.append([lm_id, cx, cy])

                xmin, xmax = min(x_coords), max(x_coords)
                ymin, ymax = min(y_coords), max(y_coords)
                bbox = (xmin, ymin, xmax, ymax)

        return lm_list, bbox

    def fingers_up(self, lm_list):
        """
        Determines which fingers are extended upward.

        :param lm_list: 21-landmark list [[id, x, y], ...].
        :return: List of 5 binary values [thumb, index, middle, ring, pinky] (1 = extended, 0 = closed).
        """
        if len(lm_list) < 21:
            return [0, 0, 0, 0, 0]

        fingers = []

        # Thumb: compare tip distance to pinky MCP vs thumb IP distance to pinky MCP
        thumb_tip_dist = math.hypot(lm_list[4][1] - lm_list[17][1], lm_list[4][2] - lm_list[17][2])
        thumb_ip_dist = math.hypot(lm_list[2][1] - lm_list[17][1], lm_list[2][2] - lm_list[17][2])
        fingers.append(1 if thumb_tip_dist > thumb_ip_dist else 0)

        # 4 Fingers: Index, Middle, Ring, Pinky
        for idx in range(1, 5):
            tip_id = self.tip_ids[idx]
            pip_id = self.pip_ids[idx]
            if lm_list[tip_id][2] < lm_list[pip_id][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def find_distance(self, p1_id, p2_id, lm_list, img=None, draw=True):
        """
        Calculates the Euclidean pixel distance between two landmarks.

        :param p1_id: Landmark ID for point 1.
        :param p2_id: Landmark ID for point 2.
        :param lm_list: 21-landmark list.
        :param img: Optional image to draw measurement indicators.
        :param draw: Whether to draw indicators on img.
        :return: (distance, img, [x1, y1, x2, y2, cx, cy])
        """
        if len(lm_list) < 21:
            return 0.0, img, [0, 0, 0, 0, 0, 0]

        x1, y1 = lm_list[p1_id][1], lm_list[p1_id][2]
        x2, y2 = lm_list[p2_id][1], lm_list[p2_id][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)

        if draw and img is not None:
            cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
            cv2.circle(img, (cx, cy), 6, (0, 0, 255), cv2.FILLED)

        return length, img, [x1, y1, x2, y2, cx, cy]

    def get_hand_scale(self, lm_list):
        """
        Calculates reference scale of the hand using distance between Wrist (0) and Middle MCP (9).
        Used to make gesture thresholds invariant to hand distance from camera.

        :param lm_list: 21-landmark list.
        :return: Hand scale factor in pixels (minimum 1.0 to prevent division by zero).
        """
        if len(lm_list) < 21:
            return 100.0

        scale = math.hypot(lm_list[0][1] - lm_list[9][1], lm_list[0][2] - lm_list[9][2])
        return max(scale, 1.0)
