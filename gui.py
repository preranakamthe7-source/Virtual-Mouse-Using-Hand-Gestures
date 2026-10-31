"""
Graphical User Interface (GUI) Module using Tkinter.
Provides a modern dashboard with live webcam feed, real-time gesture feedback,
interactive sensitivity/smoothing sliders, status indicators, and hotkey bindings.
"""

import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk

from hand_tracking import HandDetector
from mouse_controller import MouseController


class VirtualMouseGUI:
    """
    Main Tkinter application window for the Virtual Mouse project.
    Combines computer vision processing with an interactive control dashboard.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Virtual Mouse Using Hand Gestures - AI HCI Interface")
        self.root.geometry("1180x760")
        self.root.minsize(1040, 680)
        self.root.configure(bg="#121826")  # Dark modern theme

        # Initialize CV and Controller modules
        self.detector = HandDetector(max_hands=1, detection_con=0.7, track_con=0.6)
        self.mouse = MouseController(frame_width=640, frame_height=480, margin_x=100, margin_y=80)

        # Video capture & lifecycle attributes
        self.cap = None
        self.is_camera_running = False
        self.is_app_running = True
        self.video_thread = None
        self.current_frame = None
        self.fps_prev_time = 0
        self.fps = 0.0
        self.after_id = None

        # Hand tracking status
        self.hand_detected = False
        self.active_gesture_text = "Idle"

        # Apply custom styling
        self._setup_styles()

        # Build UI layout
        self._build_ui()

        # Bind keyboard shortcuts for instant, easy control and safe exit
        self.root.bind("<p>", lambda event: self.toggle_mouse_control())
        self.root.bind("<P>", lambda event: self.toggle_mouse_control())
        self.root.bind("<space>", lambda event: self.toggle_mouse_control())
        self.root.bind("<Escape>", lambda event: self.on_closing())
        self.root.bind("<q>", lambda event: self.on_closing())
        self.root.bind("<Q>", lambda event: self.on_closing())
        self.root.bind("<Control-w>", lambda event: self.on_closing())
        self.root.bind("<Control-q>", lambda event: self.on_closing())
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start periodic GUI refresh loop for video display
        self.after_id = self.root.after(15, self._refresh_video_feed)

    def _setup_styles(self):
        """Configure modern dark theme TTK styles."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Palette definition
        self.colors = {
            "bg": "#121826",
            "card_bg": "#1E293B",
            "card_border": "#334155",
            "primary": "#3B82F6",
            "success": "#10B981",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "text": "#F8FAFC",
            "text_muted": "#94A3B8"
        }

        # Frame styles
        self.style.configure("Card.TFrame", background=self.colors["card_bg"])
        self.style.configure("Dark.TFrame", background=self.colors["bg"])

        # Label styles
        self.style.configure(
            "Title.TLabel",
            background=self.colors["card_bg"],
            foreground=self.colors["text"],
            font=("Segoe UI", 16, "bold")
        )
        self.style.configure(
            "Subtitle.TLabel",
            background=self.colors["card_bg"],
            foreground=self.colors["text_muted"],
            font=("Segoe UI", 9)
        )
        self.style.configure(
            "Header.TLabel",
            background=self.colors["card_bg"],
            foreground=self.colors["primary"],
            font=("Segoe UI", 11, "bold")
        )
        self.style.configure(
            "Info.TLabel",
            background=self.colors["card_bg"],
            foreground=self.colors["text"],
            font=("Segoe UI", 10)
        )
        self.style.configure(
            "Muted.TLabel",
            background=self.colors["card_bg"],
            foreground=self.colors["text_muted"],
            font=("Segoe UI", 9)
        )

        # Slider styles
        self.style.configure(
            "Horizontal.TScale",
            background=self.colors["card_bg"],
            troughcolor="#334155"
        )

    def _build_ui(self):
        """Builds two-column dashboard: Video feed on left, controls and telemetry on right."""
        main_container = ttk.Frame(self.root, style="Dark.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # Configure 2-column grid
        main_container.columnconfigure(0, weight=3)  # Video column
        main_container.columnconfigure(1, weight=2)  # Controls column
        main_container.rowconfigure(0, weight=1)

        # ================= LEFT COLUMN: Video Stream Card =================
        left_card = tk.Frame(
            main_container,
            bg=self.colors["card_bg"],
            bd=1,
            relief=tk.SOLID,
            highlightbackground=self.colors["card_border"],
            highlightthickness=1
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # Video Title bar
        video_header = tk.Frame(left_card, bg=self.colors["card_bg"])
        video_header.pack(fill=tk.X, padx=16, pady=(12, 8))

        lbl_video_title = tk.Label(
            video_header,
            text="LIVE CAMERA STREAM",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text"],
            bg=self.colors["card_bg"]
        )
        lbl_video_title.pack(side=tk.LEFT)

        self.lbl_fps_badge = tk.Label(
            video_header,
            text="0 FPS",
            font=("Segoe UI", 9, "bold"),
            fg="#60A5FA",
            bg="#1E3A8A",
            padx=8,
            pady=2
        )
        self.lbl_fps_badge.pack(side=tk.RIGHT)

        # Video Canvas / Label
        self.video_display = tk.Label(
            left_card,
            bg="#0B0F19",
            text="Camera feed offline.\nClick 'Start Camera' to begin.",
            font=("Segoe UI", 12),
            fg=self.colors["text_muted"]
        )
        self.video_display.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        # Video Bottom Toolbar
        video_toolbar = tk.Frame(left_card, bg=self.colors["card_bg"])
        video_toolbar.pack(fill=tk.X, padx=16, pady=(8, 14))

        self.btn_start = tk.Button(
            video_toolbar,
            text="▶ Start Camera",
            bg=self.colors["success"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            activebackground="#059669",
            activeforeground="white",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.start_camera
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_stop = tk.Button(
            video_toolbar,
            text="⏹ Stop Camera",
            bg="#475569",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            activebackground="#334155",
            activeforeground="white",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2",
            state=tk.DISABLED,
            command=self.stop_camera
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_toggle_mouse = tk.Button(
            video_toolbar,
            text="⏸ Pause Control (P)",
            bg=self.colors["primary"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            activebackground="#2563EB",
            activeforeground="white",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.toggle_mouse_control
        )
        self.btn_toggle_mouse.pack(side=tk.RIGHT)

        # ================= RIGHT COLUMN: Dashboard & Controls =================
        right_container = tk.Frame(main_container, bg=self.colors["bg"])
        right_container.grid(row=0, column=1, sticky="nsew")

        # 1. Project Header Card
        header_card = tk.Frame(
            right_container,
            bg=self.colors["card_bg"],
            bd=1,
            relief=tk.SOLID,
            highlightbackground=self.colors["card_border"],
            highlightthickness=1
        )
        header_card.pack(fill=tk.X, pady=(0, 10), ipady=8)

        lbl_proj_title = tk.Label(
            header_card,
            text="Virtual Mouse Controller",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text"],
            bg=self.colors["card_bg"]
        )
        lbl_proj_title.pack(anchor="w", padx=16, pady=(6, 2))

        lbl_proj_desc = tk.Label(
            header_card,
            text="AI-powered touchless gesture control using MediaPipe & OpenCV",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["card_bg"]
        )
        lbl_proj_desc.pack(anchor="w", padx=16)

        # 2. Real-Time Telemetry & Status Card
        status_card = tk.Frame(
            right_container,
            bg=self.colors["card_bg"],
            bd=1,
            relief=tk.SOLID,
            highlightbackground=self.colors["card_border"],
            highlightthickness=1
        )
        status_card.pack(fill=tk.X, pady=(0, 10), ipady=6)

        tk.Label(
            status_card,
            text="SYSTEM STATUS & TELEMETRY",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["primary"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", padx=16, pady=(6, 8))

        # Status Grid inside Status Card
        grid_frame = tk.Frame(status_card, bg=self.colors["card_bg"])
        grid_frame.pack(fill=tk.X, padx=16, pady=(0, 6))

        # Camera Status
        tk.Label(grid_frame, text="Camera:", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).grid(row=0, column=0, sticky="w", pady=3)
        self.status_cam = tk.Label(grid_frame, text="Disconnected", font=("Segoe UI", 9, "bold"), fg=self.colors["danger"], bg=self.colors["card_bg"])
        self.status_cam.grid(row=0, column=1, sticky="w", padx=8, pady=3)

        # Mouse Control Status
        tk.Label(grid_frame, text="Mouse State:", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).grid(row=1, column=0, sticky="w", pady=3)
        self.status_mouse = tk.Label(grid_frame, text="ENABLED", font=("Segoe UI", 9, "bold"), fg=self.colors["success"], bg=self.colors["card_bg"])
        self.status_mouse.grid(row=1, column=1, sticky="w", padx=8, pady=3)

        # Hand Detection Status
        tk.Label(grid_frame, text="Hand Tracking:", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).grid(row=2, column=0, sticky="w", pady=3)
        self.status_hand = tk.Label(grid_frame, text="No Hand", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"])
        self.status_hand.grid(row=2, column=1, sticky="w", padx=8, pady=3)

        # Active Gesture
        tk.Label(grid_frame, text="Active Gesture:", font=("Segoe UI", 9, "bold"), fg=self.colors["text_muted"], bg=self.colors["card_bg"]).grid(row=3, column=0, sticky="w", pady=3)
        self.status_gesture = tk.Label(grid_frame, text="Idle", font=("Segoe UI", 10, "bold"), fg="#38BDF8", bg=self.colors["card_bg"])
        self.status_gesture.grid(row=3, column=1, sticky="w", padx=8, pady=3)

        # 3. Tuning & Configuration Card
        tuning_card = tk.Frame(
            right_container,
            bg=self.colors["card_bg"],
            bd=1,
            relief=tk.SOLID,
            highlightbackground=self.colors["card_border"],
            highlightthickness=1
        )
        tuning_card.pack(fill=tk.X, pady=(0, 10), ipady=6)

        tk.Label(
            tuning_card,
            text="TUNING & CALIBRATION",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["primary"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", padx=16, pady=(6, 4))

        # Sensitivity Slider
        sens_frame = tk.Frame(tuning_card, bg=self.colors["card_bg"])
        sens_frame.pack(fill=tk.X, padx=16, pady=2)
        tk.Label(sens_frame, text="Cursor Sensitivity:", font=("Segoe UI", 9), fg=self.colors["text"], bg=self.colors["card_bg"]).pack(side=tk.LEFT)
        self.lbl_sens_val = tk.Label(sens_frame, text="1.0x", font=("Segoe UI", 9, "bold"), fg=self.colors["primary"], bg=self.colors["card_bg"])
        self.lbl_sens_val.pack(side=tk.RIGHT)

        self.scale_sens = ttk.Scale(tuning_card, from_=0.5, to=2.0, value=1.0, command=self._on_sensitivity_change)
        self.scale_sens.pack(fill=tk.X, padx=16, pady=(0, 6))

        # Smoothing Slider
        smooth_frame = tk.Frame(tuning_card, bg=self.colors["card_bg"])
        smooth_frame.pack(fill=tk.X, padx=16, pady=2)
        tk.Label(smooth_frame, text="Motion Smoothing (EMA):", font=("Segoe UI", 9), fg=self.colors["text"], bg=self.colors["card_bg"]).pack(side=tk.LEFT)
        self.lbl_smooth_val = tk.Label(smooth_frame, text="4.0", font=("Segoe UI", 9, "bold"), fg=self.colors["primary"], bg=self.colors["card_bg"])
        self.lbl_smooth_val.pack(side=tk.RIGHT)

        self.scale_smooth = ttk.Scale(tuning_card, from_=1.0, to=8.0, value=4.0, command=self._on_smoothing_change)
        self.scale_smooth.pack(fill=tk.X, padx=16, pady=(0, 8))

        # 4. Gesture Reference Instructions Card
        guide_card = tk.Frame(
            right_container,
            bg=self.colors["card_bg"],
            bd=1,
            relief=tk.SOLID,
            highlightbackground=self.colors["card_border"],
            highlightthickness=1
        )
        guide_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10), ipady=4)

        tk.Label(
            guide_card,
            text="GESTURE CHEAT SHEET",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["primary"],
            bg=self.colors["card_bg"]
        ).pack(anchor="w", padx=16, pady=(6, 4))

        gestures = [
            ("☝️  Index Extended", "Move cursor across desktop screen"),
            ("🤏  Index + Thumb Pinch", "Left mouse click (debounced)"),
            ("✌️  Middle + Thumb Pinch", "Right context click"),
            ("🤙  Ring + Thumb Pinch", "Double click"),
            ("✌️  Index + Middle Up", "Scroll Mode: Move hand UP/DOWN"),
            ("⌨️  'P' Key / Spacebar", "Instant Pause / Resume mouse control"),
            ("⌨️  'ESC' Key", "Safe shutdown of camera and app")
        ]

        for gesture_title, gesture_desc in gestures:
            row = tk.Frame(guide_card, bg=self.colors["card_bg"])
            row.pack(fill=tk.X, padx=16, pady=2)
            tk.Label(row, text=gesture_title, font=("Segoe UI", 9, "bold"), fg="#E2E8F0", bg=self.colors["card_bg"], width=23, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=gesture_desc, font=("Segoe UI", 8), fg=self.colors["text_muted"], bg=self.colors["card_bg"], anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 5. Bottom Action Bar (Safe Exit)
        bottom_bar = tk.Frame(right_container, bg=self.colors["bg"])
        bottom_bar.pack(fill=tk.X)

        btn_exit = tk.Button(
            bottom_bar,
            text="✖ Exit Application (Press ESC or Q)",
            bg=self.colors["danger"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            activebackground="#DC2626",
            activeforeground="white",
            relief=tk.FLAT,
            pady=8,
            cursor="hand2",
            command=self.on_closing
        )
        btn_exit.pack(fill=tk.X)

    def _on_sensitivity_change(self, val):
        """Slider callback for cursor sensitivity."""
        s = round(float(val), 2)
        self.lbl_sens_val.config(text=f"{s:.1f}x")
        self.mouse.set_sensitivity(s)

    def _on_smoothing_change(self, val):
        """Slider callback for motion smoothing."""
        s = round(float(val), 1)
        self.lbl_smooth_val.config(text=f"{s:.1f}")
        self.mouse.set_smoothing(s)

    def toggle_mouse_control(self):
        """Toggle mouse control ON/OFF."""
        active = self.mouse.toggle_active()
        if active:
            self.status_mouse.config(text="ENABLED", fg=self.colors["success"])
            self.btn_toggle_mouse.config(text="⏸ Pause Control (P)", bg=self.colors["primary"])
        else:
            self.status_mouse.config(text="PAUSED", fg=self.colors["warning"])
            self.btn_toggle_mouse.config(text="▶ Resume Control (P)", bg=self.colors["warning"])

    def start_camera(self):
        """Opens webcam device and starts background frame processing thread."""
        if self.is_camera_running:
            return

        try:
            # Open primary webcam (index 0) with DirectShow fallback on Windows
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                # Fallback to default backend
                self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                messagebox.showerror(
                    "Webcam Not Available",
                    "Unable to access the webcam.\n\n"
                    "Possible causes:\n"
                    "1. Another program (Zoom, Teams, etc.) is using the webcam.\n"
                    "2. The camera is disconnected or privacy settings block access.\n"
                    "3. No webcam is connected to this computer."
                )
                return

            # Set camera resolution to 640x480
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            self.is_camera_running = True
            self.status_cam.config(text="Active (640x480)", fg=self.colors["success"])
            self.btn_start.config(state=tk.DISABLED, bg="#475569")
            self.btn_stop.config(state=tk.NORMAL, bg=self.colors["danger"])

            # Start video processing thread
            self.video_thread = threading.Thread(target=self._process_video_loop, daemon=True)
            self.video_thread.start()

        except Exception as e:
            messagebox.showerror("Initialization Error", f"An error occurred while starting camera:\n{str(e)}")

    def stop_camera(self):
        """Stops background video capture thread and releases camera."""
        self.is_camera_running = False

        # Asynchronously release camera in background so UI thread never freezes
        def _cleanup():
            if self.cap and self.cap.isOpened():
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None

        threading.Thread(target=_cleanup, daemon=True).start()

        self.current_frame = None
        self.status_cam.config(text="Disconnected", fg=self.colors["danger"])
        self.status_hand.config(text="No Hand", fg=self.colors["text_muted"])
        self.status_gesture.config(text="Idle", fg="#38BDF8")
        self.lbl_fps_badge.config(text="0 FPS")

        self.btn_start.config(state=tk.NORMAL, bg=self.colors["success"])
        self.btn_stop.config(state=tk.DISABLED, bg="#475569")

        self.video_display.config(
            image="",
            text="Camera stopped.\nClick 'Start Camera' to resume.",
            font=("Segoe UI", 12),
            fg=self.colors["text_muted"]
        )

    def _process_video_loop(self):
        """Background thread worker for capturing frames and running gesture algorithms."""
        while self.is_app_running and self.is_camera_running and self.cap and self.cap.isOpened():
            success, frame = self.cap.read()
            if not success or frame is None or not self.is_app_running:
                time.sleep(0.01)
                continue

            # Mirror the frame horizontally for natural intuitive interaction
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Calculate FPS
            curr_time = time.time()
            if self.fps_prev_time > 0:
                delta = curr_time - self.fps_prev_time
                if delta > 0:
                    self.fps = 0.9 * self.fps + 0.1 * (1.0 / delta)
            self.fps_prev_time = curr_time

            # Draw visual active margin box (where hand movement maps to screen edges)
            margin_x = self.mouse.margin_x
            margin_y = self.mouse.margin_y
            cv2.rectangle(
                frame,
                (margin_x, margin_y),
                (w - margin_x, h - margin_y),
                (255, 200, 0),
                2
            )
            cv2.putText(
                frame,
                "Active Screen Area",
                (margin_x + 5, margin_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 200, 0),
                1
            )

            # Detect hand landmarks
            frame = self.detector.find_hands(frame, draw=True)
            lm_list, _ = self.detector.find_positions(frame)

            detected_gesture = "Idle"

            if len(lm_list) >= 21:
                self.hand_detected = True
                hand_scale = self.detector.get_hand_scale(lm_list)
                fingers = self.detector.fingers_up(lm_list)

                # Landmark Tip Coordinates
                idx_x, idx_y = lm_list[8][1], lm_list[8][2]      # Index finger tip
                mid_x, mid_y = lm_list[12][1], lm_list[12][2]    # Middle finger tip
                ring_x, ring_y = lm_list[16][1], lm_list[16][2]  # Ring finger tip
                thumb_x, thumb_y = lm_list[4][1], lm_list[4][2]  # Thumb tip

                # Measure pinch distances
                dist_idx_thumb, frame, _ = self.detector.find_distance(4, 8, lm_list, frame, draw=False)
                dist_mid_thumb, frame, _ = self.detector.find_distance(4, 12, lm_list, frame, draw=False)
                dist_ring_thumb, frame, _ = self.detector.find_distance(4, 16, lm_list, frame, draw=False)

                # --- GESTURE EVALUATION PIPELINE ---

                # 1. SCROLL MODE: Index and Middle fingers extended upward together, Ring and Pinky folded
                if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                    self.mouse.handle_scrolling(idx_y)
                    detected_gesture = self.mouse.current_gesture

                    # Visual feedback: draw green line connecting index and middle tips
                    cv2.line(frame, (idx_x, idx_y), (mid_x, mid_y), (0, 255, 255), 3)
                    cv2.circle(frame, (idx_x, idx_y), 8, (0, 255, 255), cv2.FILLED)
                    cv2.circle(frame, (mid_x, mid_y), 8, (0, 255, 255), cv2.FILLED)

                # 2. DOUBLE CLICK: Ring finger and Thumb pinched together
                elif (dist_ring_thumb / hand_scale) < 0.28:
                    self.mouse.exit_scroll_mode()
                    self.mouse.handle_double_click(dist_ring_thumb, hand_scale)
                    detected_gesture = "Double Click"
                    cv2.circle(frame, (ring_x, ring_y), 10, (255, 0, 255), cv2.FILLED)
                    cv2.circle(frame, (thumb_x, thumb_y), 10, (255, 0, 255), cv2.FILLED)

                # 3. RIGHT CLICK: Middle finger and Thumb pinched together
                elif (dist_mid_thumb / hand_scale) < 0.28:
                    self.mouse.exit_scroll_mode()
                    self.mouse.handle_right_click(dist_mid_thumb, hand_scale)
                    detected_gesture = "Right Click"
                    cv2.circle(frame, (mid_x, mid_y), 10, (0, 165, 255), cv2.FILLED)
                    cv2.circle(frame, (thumb_x, thumb_y), 10, (0, 165, 255), cv2.FILLED)

                # 4. LEFT CLICK: Index finger and Thumb pinched together
                elif (dist_idx_thumb / hand_scale) < 0.28:
                    self.mouse.exit_scroll_mode()
                    self.mouse.handle_left_click(dist_idx_thumb, hand_scale)
                    detected_gesture = "Left Click"
                    cv2.circle(frame, (idx_x, idx_y), 10, (0, 255, 0), cv2.FILLED)
                    cv2.circle(frame, (thumb_x, thumb_y), 10, (0, 255, 0), cv2.FILLED)

                # 5. MOUSE MOVEMENT: Index finger extended
                elif fingers[1] == 1:
                    self.mouse.exit_scroll_mode()
                    self.mouse.move_cursor(idx_x, idx_y)
                    detected_gesture = "Cursor Moving"

                    # Visual cursor indicator on camera feed
                    cv2.circle(frame, (idx_x, idx_y), 12, (255, 0, 0), 2)
                    cv2.circle(frame, (idx_x, idx_y), 5, (0, 255, 255), cv2.FILLED)

                else:
                    self.mouse.exit_scroll_mode()
                    detected_gesture = "Neutral Hand"

            else:
                self.hand_detected = False
                self.mouse.exit_scroll_mode()
                detected_gesture = "No Hand Detected"

            self.active_gesture_text = detected_gesture

            # Draw HUD Status Bar on camera frame
            mode_color = (0, 255, 0) if self.mouse.is_active else (0, 165, 255)
            mode_text = "MOUSE: ON" if self.mouse.is_active else "MOUSE: PAUSED"
            cv2.rectangle(frame, (10, 10), (220, 42), (20, 20, 20), cv2.FILLED)
            cv2.putText(frame, mode_text, (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)

            # Store processed frame for UI thread
            self.current_frame = frame
            time.sleep(0.01)

    def _refresh_video_feed(self):
        """Main thread callback that refreshes Tkinter image and telemetry widgets."""
        if not self.is_app_running:
            return

        if self.is_camera_running and self.current_frame is not None:
            try:
                # Convert OpenCV BGR image to RGB for PIL
                frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)

                # Resize to fit preview area nicely (540x405 maintaining 4:3 aspect ratio)
                display_w = 540
                display_h = 405
                frame_resized = cv2.resize(frame_rgb, (display_w, display_h))

                img_pil = Image.fromarray(frame_resized)
                img_tk = ImageTk.PhotoImage(image=img_pil)

                self.video_display.config(image=img_tk, text="")
                self.video_display.image = img_tk  # Keep reference to avoid garbage collection

                # Update Telemetry Labels
                self.lbl_fps_badge.config(text=f"{int(self.fps)} FPS")
                self.status_hand.config(
                    text="Hand Detected" if self.hand_detected else "No Hand",
                    fg=self.colors["success"] if self.hand_detected else self.colors["text_muted"]
                )
                self.status_gesture.config(text=self.active_gesture_text)

            except Exception:
                pass

        # Schedule next refresh only if app is still running (~60 Hz UI update)
        if self.is_app_running:
            self.after_id = self.root.after(15, self._refresh_video_feed)

    def on_closing(self):
        """Immediate, foolproof application termination."""
        # 1. Immediately disable mouse and camera flags
        self.mouse.set_active(False)
        self.is_app_running = False
        self.is_camera_running = False

        # 2. Instantly hide the window so the user sees it close immediately
        try:
            self.root.withdraw()
        except Exception:
            pass

        # 3. Cancel scheduled UI refresh callback
        try:
            if self.after_id:
                self.root.after_cancel(self.after_id)
        except Exception:
            pass

        # 4. Asynchronously release camera & OpenCV resources without blocking main thread
        def _release_res():
            try:
                if self.cap and self.cap.isOpened():
                    self.cap.release()
            except Exception:
                pass
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

        threading.Thread(target=_release_res, daemon=True).start()

        # 5. Quit and destroy Tkinter UI
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

        # 6. Unconditional process exit so no background Windows DirectShow COM threads hang
        time.sleep(0.05)
        os._exit(0)
