# gives you the coordinate of four points, to used in fieldcorners

import cv2

points = []

def click_event(event, x, y, flags, param):
    """Handles mouse click events to store four points."""
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append([x, y])
        print(f"Point {len(points)}: ({x}, {y})")

        # Draw a circle on the selected point
        cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
        cv2.imshow("Image", img)

        # Stop selecting after 4 points
        if len(points) == 4:
            print("Selected points:", points)
            cv2.destroyAllWindows()
            quit()

# Load image
image_path = "top-down.png"  # Change to your image path
img = cv2.imread(image_path)

# Display image and set up mouse callback
cv2.imshow("Image", img)
cv2.setMouseCallback("Image", click_event)

cv2.waitKey(0)
cv2.destroyAllWindows()
