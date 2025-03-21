import cv2

# Input video file
input_video = "/Users/colinhaine/Desktop/yolo-env/Captures/2025azgl_qm1.mp4"
output_image = "first_frame.jpg"

# Open video
cap = cv2.VideoCapture(input_video)
cap.set(cv2.CAP_PROP_POS_FRAMES, 1000) 

# Read the first frame
ret, frame = cap.read()

if ret:
    cv2.imwrite(output_image, frame)  # Save frame as image
    print(f"First frame saved as {output_image}")
else:
    print("Failed to read the first frame.")

# Release resources
cap.release()
cv2.destroyAllWindows()
