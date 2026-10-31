"""
Mouse Controller Module using PyAutoGUI.
Handles coordinate interpolation, jitter smoothing, click debounce logic,
scrolling mechanics, and sensitivity controls.
"""

import time
import numpy as np
import pyautogui

# Set PyAutoGUI settings for ultra-responsive control
pyautogui.PAUSE = 0.001  # Remove default 0.1s delay for smooth 60 FPS motion
pyautogui.FAILSAFE = False  # Disable corner fail-safe so user can click corner buttons (Close / Start)


class MouseController:
    """
    Translates hand gestures and landmark positions into operating system
    mouse events such as cursor movement, left click, right click,
    double click, and scrolling.
    """

    def __init__(self, frame_width=640, frame_height=480, margin_x=100, margin_y=80):
        """
        Initialize the mouse controller.

        :param frame_width: Width of the webcam image.
        :param frame_height: Height of the webcam image.
        :param margin_x: Inward horizontal margin for screen edge reachability.
        :param margin_y: Inward vertical margin for screen edge reachability.
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.margin_x = margin_x
        self.margin_y = margin_y

        # Screen resolution
        self.screen_width, self.screen_height = pyautogui.size()

        # Smoothing and sensitivity
        self.smooth_factor = 4.0   # Higher = smoother but more lag (2.0 to 10.0)
        self.sensitivity = 1.0     # Multiplier for cursor movement
        self.prev_x = self.screen_width / 2.0
        self.prev_y = self.screen_height / 2.0

        # State flags to prevent machine-gun clicking
        self.left_clicked = False
        self.right_clicked = False
        self.double_clicked = False

        # Scrolling state
        self.in_scroll_mode = False
        self.scroll_anchor_y = None
        self.scroll_deadzone = 18  # Minimum pixel displacement to trigger scroll
        self.scroll_speed = 35     # PyAutoGUI scroll units per step

        # Global enable/pause flag
        self.is_active = True

        # Last gesture display string
        self.current_gesture = "Idle"

    def set_active(self, active: bool):
        """Enable or disable mouse actions."""
        self.is_active = active
        if not active:
            self.current_gesture = "Mouse Control Paused"

    def toggle_active(self) -> bool:
        """Toggle mouse control ON/OFF."""
        self.set_active(not self.is_active)
        return self.is_active

    def set_smoothing(self, value: float):
        """Update smoothing factor (2 to 10)."""
        self.smooth_factor = max(1.0, float(value))

    def set_sensitivity(self, value: float):
        """Update sensitivity multiplier (0.5 to 2.0)."""
        self.sensitivity = max(0.2, float(value))

    def move_cursor(self, raw_x, raw_y):
        """
        Interpolates camera coordinates to screen coordinates with smoothing.

        :param raw_x: X coordinate of index finger tip in camera frame.
        :param raw_y: Y coordinate of index finger tip in camera frame.
        :return: (smoothed_screen_x, smoothed_screen_y)
        """
        if not self.is_active:
            return self.prev_x, self.prev_y

        # Map active rectangle to full screen dimensions
        mapped_x = np.interp(
            raw_x,
            [self.margin_x, self.frame_width - self.margin_x],
            [0, self.screen_width]
        )
        mapped_y = np.interp(
            raw_y,
            [self.margin_y, self.frame_height - self.margin_y],
            [0, self.screen_height]
        )

        # Apply sensitivity scaling relative to center
        if self.sensitivity != 1.0:
            center_x = self.screen_width / 2.0
            center_y = self.screen_height / 2.0
            mapped_x = center_x + (mapped_x - center_x) * self.sensitivity
            mapped_y = center_y + (mapped_y - center_y) * self.sensitivity

        # Constrain to visible screen bounds (keep 2px inside to guarantee Windows click registration)
        clamped_x = np.clip(mapped_x, 2, self.screen_width - 3)
        clamped_y = np.clip(mapped_y, 2, self.screen_height - 3)

        # Exponential Moving Average Smoothing: S_t = S_{t-1} + (X_t - S_{t-1}) / smooth_factor
        curr_x = self.prev_x + (clamped_x - self.prev_x) / self.smooth_factor
        curr_y = self.prev_y + (clamped_y - self.prev_y) / self.smooth_factor

        try:
            pyautogui.moveTo(int(curr_x), int(curr_y))
        except Exception:
            pass

        self.prev_x, self.prev_y = curr_x, curr_y
        self.current_gesture = "Cursor Moving"
        return curr_x, curr_y

    def handle_left_click(self, distance, hand_scale):
        """
        Detects pinch between Index Finger (8) and Thumb (4).
        Performs a single left click with debounce and standard press duration.
        """
        if not self.is_active:
            return

        normalized_dist = distance / hand_scale
        pinch_threshold = 0.28
        release_threshold = 0.38

        if normalized_dist < pinch_threshold:
            if not self.left_clicked:
                try:
                    # Press and release with 40ms duration for Windows title bar & UI registration
                    pyautogui.mouseDown(button='left')
                    time.sleep(0.04)
                    pyautogui.mouseUp(button='left')
                except Exception:
                    try:
                        pyautogui.leftClick()
                    except Exception:
                        pass
                self.left_clicked = True
                self.current_gesture = "Left Click"
        elif normalized_dist > release_threshold:
            self.left_clicked = False

    def handle_right_click(self, distance, hand_scale):
        """
        Detects pinch between Middle Finger (12) and Thumb (4).
        Performs a single right click with debounce.
        """
        if not self.is_active:
            return

        normalized_dist = distance / hand_scale
        pinch_threshold = 0.28
        release_threshold = 0.38

        if normalized_dist < pinch_threshold:
            if not self.right_clicked:
                try:
                    pyautogui.mouseDown(button='right')
                    time.sleep(0.04)
                    pyautogui.mouseUp(button='right')
                except Exception:
                    try:
                        pyautogui.rightClick()
                    except Exception:
                        pass
                self.right_clicked = True
                self.current_gesture = "Right Click"
        elif normalized_dist > release_threshold:
            self.right_clicked = False

    def handle_double_click(self, distance, hand_scale):
        """
        Detects pinch between Ring Finger (16) and Thumb (4).
        Performs a double click with debounce.
        """
        if not self.is_active:
            return

        normalized_dist = distance / hand_scale
        pinch_threshold = 0.28
        release_threshold = 0.38

        if normalized_dist < pinch_threshold:
            if not self.double_clicked:
                try:
                    pyautogui.doubleClick()
                except Exception:
                    pass
                self.double_clicked = True
                self.current_gesture = "Double Click"
        elif normalized_dist > release_threshold:
            self.double_clicked = False

    def handle_scrolling(self, raw_y):
        """
        Handles scrolling when Index and Middle fingers are extended.
        Tracks vertical hand displacement from anchor position.

        :param raw_y: Y coordinate of hand midpoint / index tip.
        """
        if not self.is_active:
            return

        if not self.in_scroll_mode or self.scroll_anchor_y is None:
            self.in_scroll_mode = True
            self.scroll_anchor_y = raw_y
            self.current_gesture = "Scroll Mode (Neutral)"
            return

        delta_y = raw_y - self.scroll_anchor_y

        if delta_y < -self.scroll_deadzone:
            # Hand moved upward -> Scroll UP
            try:
                pyautogui.scroll(self.scroll_speed)
            except Exception:
                pass
            self.current_gesture = "Scrolling UP"
        elif delta_y > self.scroll_deadzone:
            # Hand moved downward -> Scroll DOWN
            try:
                pyautogui.scroll(-self.scroll_speed)
            except Exception:
                pass
            self.current_gesture = "Scrolling DOWN"
        else:
            self.current_gesture = "Scroll Mode (Hold)"

    def exit_scroll_mode(self):
        """Resets scroll mode anchor when gesture ceases."""
        self.in_scroll_mode = False
        self.scroll_anchor_y = None
