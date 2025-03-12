# the main file. 
# from an image (frame), it a trained YOLO to detect robots
# then for each robot it tries to get the bumper number
# two windows will pop up showing the detections

print("imports...")
import json
import cv2
from ultralytics import YOLO
import numpy as np
import easyocr

cap = cv2.VideoCapture("../Captures/elims_13.mp4")
cap.set(cv2.CAP_PROP_POS_MSEC, 15000)

field_reference = cv2.imread("top-down.png")
# image = field_reference.copy() # used for the numbers

# some constants:
colors = {"red": (0, 0, 225), "blue": (255, 0, 0)}
confidence_threshold = 0.5

print("setting up models...")
model = YOLO("ventura-best.pt") #robot detection model
# reader = easyocr.Reader(['en'], recog_network='english_g2', user_network_directory=None) #text detection model

allcorners = json.load(open(f"fieldcorners.json", 'r'))
# fieldcorners: the top down diagram
fullfieldcorners = allcorners["fullfieldcorners"]
leftfieldcorners = allcorners["leftfieldcorners"]
rightfieldcorners = allcorners["rightfieldcorners"]
# framecorners: the video
fullframecorners = allcorners["fullframecorners"]
leftframecorners = allcorners["leftframecorners"]
rightframecorners = allcorners["rightframecorners"]

# get perspective matricies to convert between the top down and camera perspectives
fullmatrix = cv2.getPerspectiveTransform(np.array(fullframecorners, dtype="float32"), np.array(fullfieldcorners, dtype="float32"))
leftmatrix = cv2.getPerspectiveTransform(np.array(leftframecorners, dtype="float32"), np.array(leftfieldcorners, dtype="float32"))
rightmatrix = cv2.getPerspectiveTransform(np.array(rightframecorners, dtype="float32"), np.array(rightfieldcorners, dtype="float32"))

print("detecting")
# do the detections
while True:    
    ret, frame = cap.read()
    if not ret:
        break
    
    field = field_reference.copy()

    results = model(frame, device="mps", verbose=False, iou=0.8)
    result = results[0]
    bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
    confidences = np.array(result.boxes.conf.cpu())
    classes = np.array(result.boxes.cls.cpu(), dtype="int")
    robots = []
    # each item in robots is a detection.
    # [0: id, 1: center cord, 2: color, 3: confidence, 4: bbox top-left, 5: bbox bottom-right, 6: detected number]

    id = 0
    for cls, bbox, conf in zip(classes, bboxes, confidences):
        (x1, y1, x2, y2) = bbox
        cord = (int((x1 + x2) / 2), int((y1 + y2) / 2)) #get the center of the bounding box (bbox)
        if conf > confidence_threshold:
            if cls == 0:
                cv2.circle(frame, (int((x1+x2)/2), int((y2-y1)*0.6+y1)), 20, colors["blue"], 5)
                robots.append([id, cord, "blue", conf, (x1, y1), (x2, y2), 0])
            elif cls == 1:
                cv2.circle(frame, (int((x1+x2)/2), int((y2-y1)*0.6+y1)), 20, colors["red"], 5)
                robots.append([id, cord, "red", conf, (x1, y1), (x2, y2), 0])
        id += 1

    # plot out the corners on the images visually
    for corners in [fullframecorners, leftframecorners, rightframecorners]:
        for corner in corners:
            cv2.circle(frame, (corner[0], corner[1]), 10, (0, 255, 0), -1)
    for corners in [fullfieldcorners, leftfieldcorners, rightfieldcorners]:
        for corner in corners:
            cv2.circle(field, (corner[0], corner[1]), 10, (0, 255, 0), -1)

    for robot in robots:
        cord = robot[1]
        point = np.array([[cord]], dtype="float32")
        if cord[1] < 644: # detections in the top full field camera
            transformed_point = cv2.perspectiveTransform(point, fullmatrix)
            
            transformed_x, transformed_y = transformed_point[0][0]
            fixed_point = (int(transformed_x), int(transformed_y))
            cv2.circle(field, fixed_point, 20, colors[robot[2]], 5)      
            cv2.putText(field, f"{robot[0]}: {robot[6]}", fixed_point, 0, 1, (0, 0, 0), round(robot[3]*5))
        else:
            if cord[0] < 959: # detections in the left field camera
                transformed_point = cv2.perspectiveTransform(point, leftmatrix)
            else: # detections in the right field camera
                transformed_point = cv2.perspectiveTransform(point, rightmatrix)
            
            transformed_x, transformed_y = transformed_point[0][0]
            fixed_point = (int(transformed_x), int(transformed_y))
            cv2.circle(field, fixed_point, 20, colors[robot[2]], -1)      
            cv2.putText(field, f"{robot[0]}: {robot[6]}", fixed_point, 0, 1, (0, 0, 0), round(robot[3]*5))

    cv2.imshow("video capture", field)
    cv2.imshow("top down view", frame)

    #go through the video as fast as possible
    if cv2.waitKey(1) == 27:
        break

    #code for frame by frame stepper
    # key = cv2.waitKey(0)
    # if key == 27:
    #     break

print("stopped.")
cap.release()
cv2.destroyAllWindows()
