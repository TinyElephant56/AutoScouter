import cv2
import os
scriptdir = os.path.dirname(os.path.abspath(__file__))

# Input and output file paths
name = "pr_7"
input_video = f"{scriptdir}/../Captures/{name}.mp4"
output_video = f"{scriptdir}/../Captures/{name}_trimmed.mp4"

# Open video
cap = cv2.VideoCapture(input_video)
fps = int(cap.get(cv2.CAP_PROP_FPS))  # Get frames per second
start_frame = 13 * fps  # Convert 13 seconds to frames

# Set start position
cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

# Get video properties
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Codec for .mp4 files
out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

# Read and save frames from 13 seconds onward
while True:
    ret, frame = cap.read()
    if not ret:
        break
    out.write(frame)

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()

print("Video trimmed successfully!")