"""
Main Application Entry Point.
Performs pre-flight environment checks, enables Windows High-DPI scaling,
initializes the Tkinter master loop, and manages clean termination.
"""

import sys
import tkinter as tk
from tkinter import messagebox

# Enable High-DPI Awareness on Windows to prevent blurry GUI rendering
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def verify_dependencies():
    """Validates that all critical third-party dependencies are installed."""
    missing = []
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")

    try:
        import mediapipe
    except ImportError:
        missing.append("mediapipe")

    try:
        import pyautogui
    except ImportError:
        missing.append("pyautogui")

    try:
        import numpy
    except ImportError:
        missing.append("numpy")

    try:
        import PIL
    except ImportError:
        missing.append("Pillow")

    if missing:
        error_msg = (
            "The following required libraries are missing:\n\n"
            + "\n".join(f"  • {pkg}" for pkg in missing)
            + "\n\nPlease run the following command in your terminal:\n\n"
            "pip install -r requirements.txt"
        )
        print("=" * 60)
        print("DEPENDENCY CHECK FAILED:")
        print(error_msg)
        print("=" * 60)

        # Attempt to show a graphical message box
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependencies", error_msg)
        root.destroy()
        sys.exit(1)


def main():
    """Application main runner."""
    # Step 1: Pre-flight check
    verify_dependencies()

    # Step 2: Import GUI after dependency verification succeeds
    from gui import VirtualMouseGUI

    # Step 3: Launch Tkinter application
    root = tk.Tk()
    app = VirtualMouseGUI(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nShutdown signal received. Exiting safely...")
        app.on_closing()


if __name__ == "__main__":
    main()
