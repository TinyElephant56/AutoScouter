# get numbers from an image

import cv2
import numpy as np
import easyocr
print("loading...")

reader = easyocr.Reader(['en'], recog_network='english_g2', user_network_directory=None)

def click_event(event, x, y, flags, param):
    global points1
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append([x, y])
        print(f"Point {len(points)}: ({x}, {y})")

        if len(points) == 2:
            print('press a key to continue')


image = cv2.imread("example.jpg")
points = []
print('click the upper left, then lower right, then any key')
cv2.imshow("Image", image)
cv2.setMouseCallback("Image", click_event)
cv2.waitKey(0)
cv2.destroyAllWindows()

print("converting...")
# points = [(617, 462), (738, 541)]
x1, y1, x2, y2 = points[0][0], points[0][1], points[1][0], points[1][1]  # Adjust based on your image
image = image[y1:y2, x1:x2]

# -----------
print("fitering...")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8, 8))
# gray = clahe.apply(gray)

gaussian = cv2.GaussianBlur(gray, (3, 3), 0)

gray = cv2.addWeighted(gray, 2.0, gaussian, -1.0, 0)

# gray = cv2.equalizeHist(gray)

gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)

# -----
print("detecting...")
text = reader.readtext(gray, detail=0, allowlist="0123456789") 
print("detected text: ",text)

cv2.imshow(f"TEXT FOUND: {text}", gray)
cv2.waitKey(0)
cv2.destroyAllWindows()

# cv2.imwrite('filtered.jpg', processed)
