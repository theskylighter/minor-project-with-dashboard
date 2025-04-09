# Driver Drowsiness Detection Project

## Overview
This project uses computer vision techniques to monitor driver alertness in real-time using a webcam. It analyzes eye blink patterns via facial landmarks to detect drowsiness and issue both visual and audible alerts.

## Features
- Real-time video capture and processing using OpenCV.
- Facial feature detection with dlib and imutils.
- Eye blink analysis to determine alertness levels.
- Audible notification using winsound when drowsiness or sleep is detected.

## Requirements
- Python 3.x
- OpenCV
- dlib
- imutils
- numpy
- winsound (Windows only)
- Pre-trained model: [shape_predictor_68_face_landmarks.dat](#) *(Download and place in project root)*

## Installation & Usage
1. Install the required libraries:
   ```
   pip install -r requirements.txt
   ```
2. Download the `shape_predictor_68_face_landmarks.dat` file and place it in the project directory.
3. Run the driver drowsiness detection script:
   ```
   python driverDrowsy.py
   ```
4. To exit the application, press the ESC key.

## Notes
- The detection thresholds in the script can be adjusted based on real-world testing and environmental conditions.
- Ensure good lighting and proper camera positioning for optimal performance.

## License
Specify your project's license information here.