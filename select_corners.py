import os
import json
import cv2
import numpy as np

# Load the image
def get_corners(scriptdir, key, event):
    margin = 100 
    
    def select_points(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            relative_x = x - margin
            relative_y = y - margin
            points.append([relative_x, relative_y])

            # Draw the selected point
            cv2.circle(padded_image, (x, y), 5, (0, 0, 255), -1)
            cv2.imshow("Select Points", padded_image)
    data = {}
    # Display the padded image
    for name in ['fullframecorners', 'leftframecorners', 'rightframecorners']:
        cap = cv2.VideoCapture(f'{scriptdir}/matches/{key}/{key}.mp4')
        cap.set(cv2.CAP_PROP_POS_MSEC, 14000)
        _, image = cap.read()
        h, w, _ = image.shape
        print(h, w)
        padded_image = np.ones((h + 2 * margin, w + 2 * margin, 3), dtype=np.uint8) * 255 
        padded_image[margin:margin + h, margin:margin + w] = image 

        points = []

        cv2.imshow(event, padded_image)
        cv2.setMouseCallback(event, select_points)

        while len(points) < 4:
            cv2.waitKey(1)
        data[name] = points
        cv2.destroyAllWindows()
    
    with open(f'{scriptdir}/events/{event}.json', 'w') as f:
        json.dump(data, f)
    print("Selected Points (relative to original image):", points)

if __name__ == "__main__":
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    get_corners(scriptdir, '2025azgl_qm65', '2025azgl')