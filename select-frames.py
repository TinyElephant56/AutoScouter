# Convert an video into multiple frames to be used as training data
# this code written by chatGPT

import cv2
import os
import random
def extract_frames(video_path, output_folder):
    # Open video file
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video.")
        return
    
    # Get video FPS (frames per second)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    frame_count = 0
    second = 15  # Start at 15 seconds
    
    while True:
        cap.set(cv2.CAP_PROP_POS_MSEC, second * 1000)  # Move to the timestamp
        success, frame = cap.read()
        
        if not success:
            break  # Stop if no more frames
        
        frame_filename = os.path.join(output_folder, f'frame_{second}.jpg')
        cv2.imwrite(frame_filename, frame)
        print(f"Saved: {frame_filename}")
        
        second += 2  # Move to the next second
    
    cap.release()
    print("Frame extraction complete.")

# Example usage
base = f"/Users/colinhaine/Desktop/yolo-env/Captures/"
path = input("vid name: ")
video_file = base+path
output_directory = f"Captures/frames/{path}"  # Folder to save frames
extract_frames(video_file, output_directory)
