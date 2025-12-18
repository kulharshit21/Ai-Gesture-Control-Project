# 🖱️ Gesture & Voice Control Application

A hand gesture and voice-controlled mouse system that allows users to control their computer using gestures and voice commands.

Built with Python and libraries like:
- MediaPipe
- OpenCV
- PyAutoGUI
- SpeechRecognition
- CustomTkinter
- pyttsx3 (Text-to-Speech)


## ✅ Features

- **Gesture-Based Mouse Control**: Navigate, scroll, click, and drag using different finger counts.
- **Voice Commands**: Perform actions like clicking, scrolling, typing, and pressing keys via voice.
- **Interactive UI**: A sleek interface built with `CustomTkinter`.
- **Smooth Cursor Movement**: Adjustable smoothing for better cursor control.
- **Log Activity**: View real-time logs of all performed actions.

## 📦 Requirements

Make sure you have the following dependencies installed:

```bash
pip install opencv-python mediapipe pyautogui speechrecognition customtkinter pyttsx3 pillow numpy
```

> ⚠️ Note: Ensure your webcam and microphone are working properly for full functionality.

---

## 🧾 Requirements File

You can create a `requirements.txt` file with the following content:

```txt
opencv-python
mediapipe
pyautogui
speechrecognition
customtkinter
pyttsx3
pillow
numpy
```

Then install them using:

```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gesture-voice-control.git
   cd gesture-voice-control
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

4. Use gestures or voice commands to interact with your PC!

---

## 🖐️ Gesture Guide

| Fingers Shown | Action                     |
|---------------|----------------------------|
| 1             | Move Cursor                |
| 2             | Scroll Up                  |
| 3             | Scroll Down                |
| 4             | Left Click                 |
| 5             | Drag Mode (Hold & Move)    |

---

## 🗣️ Voice Commands

| Command Format         | Action Performed               |
|------------------------|--------------------------------|
| "click"                | Left mouse click               |
| "right click"          | Right mouse click              |
| "double click"         | Double left click              |
| "scroll up"            | Scroll page up                 |
| "scroll down"          | Scroll page down               |
| "type [text]"          | Type the given text            |
| "press [key]"          | Press a specific key           |

---

## 📁 Project Structure

```
gesture-voice-control/
│
├── main.py                   # Main script
├── README.md                 # This README
└── requirements.txt          # Python dependencies
```

---


## 💬 Contributions

This Project is contributed my teammates Shubhangi Sharma and Sanchi Mahajan

---

## 📝 Tips for Best Experience

- Use in a well-lit environment for accurate hand detection.
- Speak clearly when giving voice commands.
- Adjust the smoothing slider according to your movement style.


