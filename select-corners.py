# lets you select corner points to be used in fieldcorners.json
# coded by chatgpt


import cv2
import numpy as np

# Load the image
image = cv2.imread("top-down.png")
h, w, _ = image.shape

print(h, w)
margin = 100  # Margin around the image

# Create a new larger image with padding
padded_image = np.ones((h + 2 * margin, w + 2 * margin, 3), dtype=np.uint8) * 255  # White background
padded_image[margin:margin + h, margin:margin + w] = image  # Place the original image in the center

points = []  # Store selected points

def select_points(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Convert coordinates relative to the original image
        relative_x = x - margin
        relative_y = y - margin
        points.append([relative_x, relative_y])

        # Draw the selected point
        cv2.circle(padded_image, (x, y), 5, (0, 0, 255), -1)
        cv2.imshow("Select Points", padded_image)

# Display the padded image
cv2.imshow("Select Points", padded_image)
cv2.setMouseCallback("Select Points", select_points)

# Wait for user to select 4 points
while len(points) < 4:
    cv2.waitKey(1)

cv2.destroyAllWindows()

print("Selected Points (relative to original image):", points)
