# Virtual Mouse Using Hand Gestures (Python & MediaPipe)

An AI-powered Human-Computer Interaction (HCI) desktop application that allows users to control their operating system cursor, execute clicks, and scroll documents using real-time webcam hand gestures—completely eliminating the need for a physical mouse.

---

## 🌟 Key Features

- **Real-Time Hand Landmark Tracking**: Tracks 21 3D hand joints at 30+ FPS using Google's MediaPipe Hands pipeline.
- **Natural Cursor Navigation**: Translates index finger tip motion into cursor coordinates across the full display.
- **Edge Reachability with Active Margins**: Features an inner bounding box so users can reach all 4 display corners without stretching their hand outside the camera's field of view.
- **Exponential Moving Average (EMA) Smoothing**: Eliminates jitter and natural hand tremors for smooth cursor motion.
- **Debounced Click Interactions**:
  - **Left Click**: Pinch Index Finger + Thumb.
  - **Right Click**: Pinch Middle Finger + Thumb.
  - **Double Click**: Pinch Ring Finger + Thumb.
  - Includes release thresholds to prevent accidental machine-gun repeat clicks.
- **Bi-Directional Gesture Scrolling**: Extend Index and Middle fingers together and move your hand up or down to scroll web pages and documents smoothly.
- **Instant Pause / Resume Safety**: Hit the **'P'** key or Spacebar at any time to pause cursor movement while keeping tracking active.
- **Modern Tkinter Dashboard**: Clean dark-theme interface displaying live video feed, real-time FPS counter, gesture status, sensitivity sliders, and a gesture cheat sheet.
- **Robust Error Handling**: Gracefully handles camera disconnects, temporary hand occlusion, and missing libraries.

---

## 📁 Project Structure

```text
Virtual_Mouse_Project/
│
├── main.py               # Pre-flight environment check and application launcher
├── hand_tracking.py      # MediaPipe 21-landmark tracking and finger state math
├── mouse_controller.py   # Screen coordinate interpolation, EMA smoothing, and PyAutoGUI triggers
├── gui.py                # Modern Tkinter dashboard, video streaming thread, and telemetry widgets
├── requirements.txt      # Pinned, tested Python library dependencies
├── README.md             # Complete user guide, setup steps, and troubleshooting
├── PROJECT_REPORT.md     # Full academic project documentation (18 sections + Viva Q&A)
└── screenshots/          # Directory for demo and report images
```

---

## 🖐️ Gesture Cheat Sheet

| Gesture | Finger Pose | OS Action | Visual Indicator |
| :--- | :--- | :--- | :--- |
| **Move Cursor** | Index finger extended up | Cursor follows finger | Blue target circle on index tip |
| **Left Click** | Pinch Index Tip + Thumb Tip | Single Left Click | Green pinch circle & debounce |
| **Right Click** | Pinch Middle Tip + Thumb Tip | Context Menu / Right Click | Orange pinch circle |
| **Double Click** | Pinch Ring Tip + Thumb Tip | Double Left Click | Purple pinch circle |
| **Scroll Mode** | Index + Middle extended up | Move hand Up/Down to scroll | Yellow connecting line |
| **Pause/Resume** | Press **'P'** or **Spacebar** | Toggle mouse control ON/OFF | Yellow / Green HUD badge |
| **Emergency Exit** | Press **ESC** key | Safe shutdown of camera & app | Window closes cleanly |

---

## ⚙️ System Requirements

- **Operating System**: Windows 10 / 11 (64-bit), macOS, or Linux
- **Python**: Python 3.8 to 3.11 (Python 3.10 or 3.11 recommended)
- **Webcam**: Standard internal laptop webcam (720p or 480p) or USB webcam
- **Hardware**: Any modern Intel/AMD dual-core or quad-core processor (runs efficiently on standard CPU without requiring an external GPU)

---

## 🚀 Step-by-Step Installation & Execution (Windows)

### Step 1: Verify Python Installation
Open **Command Prompt** (cmd) or **PowerShell** and verify that Python is installed:
```powershell
python --version
```
*(If Python is not installed, download Python 3.11 from [python.org](https://www.python.org/downloads/) and make sure to check **"Add Python to PATH"** during installation).*

### Step 2: Open Project Directory
Navigate into the project folder:
```powershell
cd "C:\Users\Prerane kamthe\.gemini\antigravity\scratch\Virtual_Mouse_Project"
```

### Step 3: Create and Activate a Virtual Environment (Recommended)
Creating an isolated virtual environment prevents library version conflicts:
```powershell
python -m venv venv
```
Activate the environment:
- On Windows PowerShell:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- On Windows Command Prompt (cmd):
  ```cmd
  .\venv\Scripts\activate.bat
  ```

### Step 4: Upgrade pip and Install Dependencies
Install all required packages using `requirements.txt`:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Launch the Application
Run the main script:
```powershell
python main.py
```

---

## 🎮 How to Use the Application

1. **Start the Camera**:
   - Click the green **"▶ Start Camera"** button on the bottom-left toolbar.
   - The live webcam feed will appear inside the preview box.
2. **Position Your Hand**:
   - Hold your hand approximately 1.5 to 2.5 feet (45–75 cm) in front of the camera with your palm facing the lens.
   - The 21-landmark skeleton will track your fingers in real time.
3. **Move the Cursor**:
   - Raise your index finger while keeping other fingers closed. Move your index finger within the yellow active bounding box to move the mouse pointer.
4. **Perform Clicks**:
   - Bring your index finger and thumb together briefly to left-click.
   - Bring your middle finger and thumb together to right-click.
   - Bring your ring finger and thumb together to double-click a folder or app.
5. **Scroll**:
   - Raise both your index and middle fingers together (peace sign). Move your hand upward to scroll up, or downward to scroll down.
6. **Pause Cursor Control**:
   - Press the **'P'** key or click **"⏸ Pause Control"** if you need to scratch your head, type on the keyboard, or point without moving the mouse.
7. **Exit**:
   - Click the red **"✖ Exit Application"** button or press **ESC**.

---

## 🔧 Tuning Sensitivity & Smoothing

- **Cursor Sensitivity (0.5x – 2.0x)**:
  - If your screen resolution is large (e.g. 1080p, 2K, or 4K) and you want the cursor to move faster with smaller hand movements, slide sensitivity higher (e.g., `1.3x`).
  - If you want finer, more controlled movements, set it to `0.8x` or `1.0x`.
- **Motion Smoothing (EMA) (1.0 – 8.0)**:
  - Higher values (e.g. `4.0` – `6.0`) filter out hand tremors and shaky gestures for steady pointing.
  - Lower values (e.g. `2.0`) provide instantaneous, rapid cursor tracking with minimal latency.

---

## 🛠️ Troubleshooting & FAQs

### Q1: The webcam window is blank or shows "Webcam Not Available" error.
- **Solution**: Check if another application (such as Microsoft Teams, Zoom, Skype, or Windows Camera app) is using the webcam in the background. Close those apps and click **"Start Camera"** again.

### Q2: MediaPipe fails to install with error `No matching distribution found`.
- **Solution**: Ensure your Python version is 3.8 to 3.11 (64-bit). If you are using Python 3.12+, some pre-built MediaPipe wheels may not yet be compatible; install Python 3.11.

### Q3: PyAutoGUI triggers `pyautogui.FailSafeException`.
- **Solution**: PyAutoGUI features a safety failsafe where moving the cursor to the extreme top-left corner `(0, 0)` raises an exception to prevent runaway cursor loops. Our controller handles this exception safely, but you can also press **'P'** to instantly pause control.

### Q4: Hand landmarks flicker or drop tracking.
- **Solution**: Ensure adequate lighting in your room. Avoid strong backlighting (such as sitting directly in front of a bright window).
