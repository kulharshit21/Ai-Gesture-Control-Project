import cv2
import mediapipe as mp
import pyautogui
import speech_recognition as sr
import threading
import time
import tkinter as tk
import customtkinter as ctk
import pyttsx3
from PIL import Image, ImageTk
import numpy as np
from enum import Enum

# Prevent PyAutoGUI from moving the mouse to extreme edges
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# UI Constants
MODE_NAVIGATION = "🖱️ Mode: Navigation"
MODE_SCROLL_UP = "📜 Mode: Scroll Up"
MODE_SCROLL_DOWN = "📜 Mode: Scroll Down"
MODE_CLICK = "👆 Mode: Click"
MODE_DRAG = "✋ Mode: Drag"
VOICE_INACTIVE = "🎤 Voice: Inactive"
VOICE_ACTIVE = "🎤 Voice: Active"
VOICE_LISTENING = "🎤 Voice: Listening..."
VOICE_PROCESSING = "🎤 Voice: Processing..."
VOICE_ERROR = "🎤 Voice: Error"
HAND_DETECTED = "👋 Hand: Detected"
HAND_NOT_DETECTED = "👋 Hand: Not Detected"
BTN_START_TRACKING = "Start Tracking"
BTN_STOP_TRACKING = "Stop Tracking"
BTN_START_VOICE = "Start Voice Control"
BTN_STOP_VOICE = "Stop Voice Control"

class Mode(Enum):
    NAVIGATION = 1
    SCROLL_UP = 2
    SCROLL_DOWN = 3
    CLICK = 4
    DRAG = 5

class GestureVoiceControlApp:
    def __init__(self, root):
        # Main window setup
        self.root = root
        self.root.title("Simplified Gesture & Voice Control")
        self.root.geometry("1000x680")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize variables
        self.running = False
        self.voice_running = False
        self.mode = Mode.NAVIGATION
        self.prev_y = None
        self.smoothing = 5
        self.history_x = []
        self.history_y = []
        self.screen_width, self.screen_height = pyautogui.size()
        self.click_cooldown = 0
        self.last_finger_count = 0
        self.finger_count_history = []  # For stabilizing finger count detection
        self.is_dragging = False
        self.drag_start_pos = None
        
        # Speech recognition setup
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        
        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.6,  # Lower threshold for better detection
            min_tracking_confidence=0.6    # Lower threshold for better tracking
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Create UI
        self.create_ui()
        
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.log_message("Error: Could not open webcam")
            return
        
        # Set capture properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Success message
        self.log_message("Application initialized successfully")
        self.speak_text("Simplified Gesture Control is ready")
        
    def create_ui(self):
        # Main container
        container = ctk.CTkFrame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel
        left_panel = ctk.CTkFrame(container, width=640)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Camera frame
        self.camera_label = ctk.CTkLabel(left_panel, text="", height=480)
        self.camera_label.pack(pady=10)
        
        # Status indicators in a frame
        status_frame = ctk.CTkFrame(left_panel)
        status_frame.pack(fill=tk.X, pady=5)
        
        # Hand status indicator
        self.hand_status = ctk.CTkLabel(status_frame, text=HAND_NOT_DETECTED, font=("Arial", 14))
        self.hand_status.pack(side=tk.LEFT, padx=20)
        
        # Current mode display
        self.mode_label = ctk.CTkLabel(status_frame, text=MODE_NAVIGATION, font=("Arial", 14))
        self.mode_label.pack(side=tk.LEFT, padx=20)
        
        # Voice status indicator
        self.voice_status = ctk.CTkLabel(status_frame, text=VOICE_INACTIVE, font=("Arial", 14))
        self.voice_status.pack(side=tk.LEFT, padx=20)
        
        # Right panel
        right_panel = ctk.CTkFrame(container, width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        
        # Control title
        ctk.CTkLabel(right_panel, text="Controls", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Control buttons
        self.start_button = ctk.CTkButton(right_panel, text=BTN_START_TRACKING, command=self.toggle_tracking)
        self.start_button.pack(fill=tk.X, padx=20, pady=5)
        
        self.voice_button = ctk.CTkButton(right_panel, text=BTN_START_VOICE, command=self.toggle_voice)
        self.voice_button.pack(fill=tk.X, padx=20, pady=5)
        
        # Sensitivity control
        sensitivity_frame = ctk.CTkFrame(right_panel)
        sensitivity_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ctk.CTkLabel(sensitivity_frame, text="Smoothing:").pack(side=tk.LEFT, padx=5)
        
        self.smooth_slider = ctk.CTkSlider(sensitivity_frame, from_=1, to=10, number_of_steps=9, 
                                          command=self.update_smoothing)
        self.smooth_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)
        self.smooth_slider.set(self.smoothing)
        
        # Help section
        help_frame = ctk.CTkFrame(right_panel)
        help_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(help_frame, text="Gesture Guide", font=("Arial", 14, "bold")).pack(pady=5)
        
        gestures = [
            "☝️ One finger: Navigate cursor",
            "✌️ Two fingers: Scroll up",
            "👌 Three fingers: Scroll down",
            "🖖 Four fingers: Click",
            "✋ Five fingers: Drag up/down"
        ]
        
        for gesture in gestures:
            ctk.CTkLabel(help_frame, text=gesture, anchor="w").pack(fill=tk.X, padx=5, pady=3)
        
        ctk.CTkLabel(help_frame, text="Voice Commands", font=("Arial", 14, "bold")).pack(pady=5)
        
        commands = [
            "\"Click\": Left click",
            "\"Right click\": Right click",
            "\"Double click\": Double click",
            "\"Scroll up/down\": Scroll page",
            "\"Type [text]\": Type text",
            "\"Press [key]\": Press keyboard key"
        ]
        
        for cmd in commands:
            ctk.CTkLabel(help_frame, text=cmd, anchor="w").pack(fill=tk.X, padx=5, pady=3)
        
        # Log area
        log_frame = ctk.CTkFrame(right_panel)
        log_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ctk.CTkLabel(log_frame, text="Activity Log", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.log_area = ctk.CTkTextbox(log_frame, height=100, state="disabled")
        self.log_area.pack(fill=tk.X)
    
    def update_smoothing(self, value):
        self.smoothing = int(value)
        
    def log_message(self, message):
        """Add message to log area with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_area.configure(state="normal")
        self.log_area.insert(tk.END, log_entry)
        self.log_area.see(tk.END)
        self.log_area.configure(state="disabled")
        
    def speak_text(self, text):
        """Speak the given text using TTS"""
        threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()
    
    def _speak_worker(self, text):
        """Background worker for text-to-speech"""
        self.engine.say(text)
        self.engine.runAndWait()
    
    def toggle_tracking(self):
        """Toggle hand tracking on/off"""
        if self.running:
            self.running = False
            self.start_button.configure(text=BTN_START_TRACKING)
            self.log_message("Hand tracking stopped")
        else:
            self.running = True
            self.start_button.configure(text=BTN_STOP_TRACKING)
            self.log_message("Hand tracking started")
            threading.Thread(target=self.run_tracking, daemon=True).start()
    
    def toggle_voice(self):
        """Toggle voice control on/off"""
        if self.voice_running:
            self.voice_running = False
            self.voice_button.configure(text=BTN_START_VOICE)
            self.voice_status.configure(text=VOICE_INACTIVE)
            self.log_message("Voice control stopped")
        else:
            self.voice_running = True
            self.voice_button.configure(text=BTN_STOP_VOICE)
            self.voice_status.configure(text=VOICE_ACTIVE)
            self.log_message("Voice control started")
            threading.Thread(target=self.run_voice_recognition, daemon=True).start()
    
    def run_voice_recognition(self):
        """Voice recognition thread"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        while self.voice_running:
            try:
                with self.microphone as source:
                    self.voice_status.configure(text=VOICE_LISTENING)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    self.voice_status.configure(text=VOICE_PROCESSING)
                
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    self.log_message(f"Voice command: {text}")
                    self.process_voice_command(text)
                except sr.UnknownValueError:
                    self.voice_status.configure(text=VOICE_ACTIVE)
                except sr.RequestError:
                    self.log_message("Could not request results from Google Speech Recognition")
                    self.voice_status.configure(text=VOICE_ERROR)
                    time.sleep(2)
                    self.voice_status.configure(text=VOICE_ACTIVE)
            
            except Exception as e:
                self.log_message(f"Voice error: {str(e)}")
                self.voice_status.configure(text=VOICE_ERROR)
                time.sleep(2)
                self.voice_status.configure(text=VOICE_ACTIVE)
    
    def process_voice_command(self, command):
        """Process voice commands"""
        # Command to click
        if command in ["click", "click mouse", "left click"]:
            pyautogui.click()
            self.log_message("Left click")
        
        # Command for right click
        elif command in ["right click", "right mouse"]:
            pyautogui.rightClick()
            self.log_message("Right click")
        
        # Double click command
        elif command in ["double click", "double"]:
            pyautogui.doubleClick()
            self.log_message("Double click")
        
        # Scrolling commands
        elif "scroll" in command:
            if "up" in command:
                pyautogui.scroll(300)  # Scroll up
                self.log_message("Scrolling up")
            elif "down" in command:
                pyautogui.scroll(-300)  # Scroll down
                self.log_message("Scrolling down")
        
        # Typing commands
        elif command.startswith("type "):
            text_to_type = command[5:]  # Remove "type " prefix
            pyautogui.write(text_to_type)
            self.log_message(f"Typing: {text_to_type}")
        
        # Key press commands
        elif command.startswith("press "):
            key = command[6:]  # Remove "press " prefix
            
            # Handle special keys
            special_keys = {
                "enter": "enter", "space": "space", "tab": "tab",
                "escape": "escape", "esc": "escape",
                "up": "up", "down": "down", "left": "left", "right": "right",
                "backspace": "backspace", "delete": "delete",
                "home": "home", "end": "end",
                "page up": "pageup", "page down": "pagedown"
            }
            
            if key in special_keys:
                pyautogui.press(special_keys[key])
                self.log_message(f"Pressed {key} key")
            else:
                # For single character keys
                pyautogui.press(key)
                self.log_message(f"Pressed {key} key")
        
        # Respond to greeting
        elif command in ["hello", "hi there", "hey"]:
            self.speak_text("Hello, I'm listening to your commands")
    
    def run_tracking(self):
        """Main tracking thread for hand gesture recognition"""
        last_mode_change_time = time.time() - 1  # Initialize with offset to allow immediate mode change
        mode_change_cooldown = 0.5  # Seconds between mode changes to prevent rapid switching
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.log_message("Error reading from webcam")
                break
            
            # Flip the frame horizontally for a more intuitive mirror view
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB for MediaPipe and process for hand detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            # Check if hand is detected
            if not results.multi_hand_landmarks:
                self.handle_no_hand_detected()
                self.update_canvas(frame)
                continue
            
            # Hand is detected - process landmarks
            self.hand_status.configure(text=HAND_DETECTED)
            self.process_hand_landmarks(frame, results, last_mode_change_time)
            last_mode_change_time = self.update_mode_if_needed(last_mode_change_time, mode_change_cooldown)
            
            # Display the processed frame
            self.update_canvas(frame)
            
            # Handle click cooldown
            if self.click_cooldown > 0:
                self.click_cooldown -= 1
    
    def handle_no_hand_detected(self):
        """Handle case when no hand is detected"""
        self.hand_status.configure(text=HAND_NOT_DETECTED)
        self.finger_count_history = []
        # Clear pointer smoothing history when hand disappears
        self.history_x = []
        self.history_y = []
        self.prev_y = None
        
        # End dragging if active
        if self.is_dragging:
            pyautogui.mouseUp()
            self.is_dragging = False
            self.log_message("Drag ended (hand lost)")
    
    def process_hand_landmarks(self, frame, results, last_mode_change_time):
        """Process detected hand landmarks"""
        # Process only the first detected hand
        hand_landmarks = results.multi_hand_landmarks[0]
        
        # Draw landmarks on frame
        self.mp_draw.draw_landmarks(
            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        
        # Extract landmark positions
        landmarks = []
        for lm in hand_landmarks.landmark:
            x, y = int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])
            landmarks.append((x, y))
        
        # Count extended fingers and stabilize
        finger_count = self.count_fingers(landmarks)
        self.update_finger_count_history(finger_count)
        
        # Get most common finger count from history for stability
        common_finger_count = self.get_common_finger_count()
        
        # Add finger count text to frame
        cv2.putText(frame, f"Fingers: {common_finger_count}", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Process according to current mode
        self.process_current_mode(common_finger_count, landmarks)
    
    def update_finger_count_history(self, finger_count):
        """Update history of finger counts for stabilization"""
        self.finger_count_history.append(finger_count)
        if len(self.finger_count_history) > 5:  # Keep last 5 frames
            self.finger_count_history.pop(0)
    
    def get_common_finger_count(self):
        """Get most common finger count from recent history"""
        if not self.finger_count_history:
            return 0
        return max(set(self.finger_count_history), key=self.finger_count_history.count)
    
    def update_mode_if_needed(self, last_mode_change_time, cooldown):
        """Update mode if finger count has changed and cooldown passed"""
        common_finger_count = self.get_common_finger_count()
        
        if common_finger_count != self.last_finger_count and time.time() - last_mode_change_time > cooldown:
            self.handle_finger_count_change(common_finger_count)
            self.last_finger_count = common_finger_count
            return time.time()  # Reset cooldown timer
        
        return last_mode_change_time  # Keep current cooldown timer
    
    def process_current_mode(self, finger_count, landmarks):
        """Process hand gesture based on current mode"""
        if self.mode == Mode.NAVIGATION and finger_count == 1:
            self.handle_navigation_mode(landmarks)
        elif self.mode == Mode.SCROLL_UP and finger_count == 2:
            pyautogui.scroll(10)  # Scroll up with a gentle continuous movement
        elif self.mode == Mode.SCROLL_DOWN and finger_count == 3:
            pyautogui.scroll(-10)  # Scroll down with a gentle continuous movement
        elif self.mode == Mode.CLICK and finger_count == 4:
            if self.click_cooldown == 0:
                pyautogui.click()
                self.click_cooldown = 10
                self.log_message("Click performed")
        elif self.mode == Mode.DRAG and finger_count == 5:
            self.handle_drag_mode(landmarks)
    
    def count_fingers(self, landmarks):
        """Count number of extended fingers"""
        if len(landmarks) < 21:  # Need all hand landmarks
            return 0
            
        # Points for each finger tip and pip joints
        tips = [8, 12, 16, 20]  # Index, middle, ring, pinky tips
        pips = [6, 10, 14, 18]  # Corresponding pip joints
        
        # Count extended fingers (not thumb)
        count = 0
        for tip, pip in zip(tips, pips):
            # Finger is extended if tip is higher than pip (lower y-value)
            if landmarks[tip][1] < landmarks[pip][1]:  
                count += 1
                
        # Special case for thumb
        if landmarks[4][0] > landmarks[3][0] + 20:  # Thumb extended to right
            count += 1
            
        return count
    
    def handle_finger_count_change(self, finger_count):
        """Handle changes in detected finger count"""
        # End dragging if it was active and we're switching modes
        if self.is_dragging and finger_count != 5:
            pyautogui.mouseUp()
            self.is_dragging = False
            self.log_message("Drag ended (mode change)")
        
        if finger_count == 1:
            self.mode = Mode.NAVIGATION
            self.mode_label.configure(text=MODE_NAVIGATION)
            self.log_message("Switched to navigation mode")
        
        elif finger_count == 2:
            self.mode = Mode.SCROLL_UP
            self.mode_label.configure(text=MODE_SCROLL_UP)
            self.log_message("Switched to scroll up mode")
        
        elif finger_count == 3:
            self.mode = Mode.SCROLL_DOWN
            self.mode_label.configure(text=MODE_SCROLL_DOWN)
            self.log_message("Switched to scroll down mode")
        
        elif finger_count == 4:
            self.mode = Mode.CLICK
            self.mode_label.configure(text=MODE_CLICK)
            self.log_message("Switched to click mode")
            
        elif finger_count == 5:
            self.mode = Mode.DRAG
            self.mode_label.configure(text=MODE_DRAG)
            self.log_message("Switched to drag mode")
            self.prev_y = None  # Reset drag reference point
    
    def handle_navigation_mode(self, landmarks):
        """Handle mouse pointer control mode"""
        # Use index finger tip for cursor control
        index_tip = landmarks[8]
        
        # Apply smoothing to cursor movement
        self.history_x.append(index_tip[0])
        self.history_y.append(index_tip[1])
        
        # Keep history to smoothing length
        if len(self.history_x) > self.smoothing:
            self.history_x.pop(0)
            self.history_y.pop(0)
        
        # Calculate smoothed position
        if len(self.history_x) > 2:  # Need at least a few points for stability
            smooth_x = sum(self.history_x) / len(self.history_x)
            smooth_y = sum(self.history_y) / len(self.history_y)
            
            # Map camera coordinates to screen coordinates with larger margins
            # This reduces the need for precise hand positioning
            cam_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            cam_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            # Apply mapping with larger margins (120px from edges)
            screen_x = np.interp(smooth_x, [120, cam_width-120], [0, self.screen_width])
            screen_y = np.interp(smooth_y, [120, cam_height-120], [0, self.screen_height])
            
            # Move the mouse cursor with increased smoothing
            pyautogui.moveTo(screen_x, screen_y)
    
    def handle_drag_mode(self, landmarks):
        """Handle drag mode with 5 fingers"""
        # Use middle finger for drag reference
        middle_tip = landmarks[12]
        
        # Apply smoothing to movement
        self.history_x.append(middle_tip[0])
        self.history_y.append(middle_tip[1])
        
        if len(self.history_x) > self.smoothing:
            self.history_x.pop(0)
            self.history_y.pop(0)
        
        if len(self.history_x) > 2:
            smooth_x = sum(self.history_x) / len(self.history_x)
            smooth_y = sum(self.history_y) / len(self.history_y)
            
            # Map coordinates to screen
            cam_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            cam_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            screen_x = np.interp(smooth_x, [120, cam_width-120], [0, self.screen_width])
            screen_y = np.interp(smooth_y, [120, cam_height-120], [0, self.screen_height])
            
            # Start drag if not already dragging
            if not self.is_dragging:
                pyautogui.mouseDown()
                self.is_dragging = True
                self.log_message("Started dragging")
            
            # Move while dragging
            pyautogui.moveTo(screen_x, screen_y)
    
    def update_canvas(self, frame):
        """Update UI with the current camera frame"""
        # Convert frame to RGB for tkinter
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize if needed
        frame_height, frame_width = rgb_frame.shape[:2]
        max_width = 640
        
        if frame_width > max_width:
            scale_factor = max_width / frame_width
            new_width = int(frame_width * scale_factor)
            new_height = int(frame_height * scale_factor)
            rgb_frame = cv2.resize(rgb_frame, (new_width, new_height))
        
        # Convert to PhotoImage
        img = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Update the label
        self.camera_label.imgtk = imgtk
        self.camera_label.configure(image=imgtk)
    
    def on_close(self):
        """Clean up resources when application closes"""
        self.running = False
        self.voice_running = False
        
        # Make sure to release mouse if dragging
        if self.is_dragging:
            pyautogui.mouseUp()
        
        if self.cap and self.cap.isOpened():
            self.cap.release()
        
        self.root.destroy()
        
if __name__ == "__main__":
    root = ctk.CTk()
    app = GestureVoiceControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()