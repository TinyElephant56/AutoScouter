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

frame = cv2.imread("frame_36.jpg")
field = cv2.imread("top-down.png")
image = frame.copy() # used for the numbers

# some constants:
colors = {"red": (0, 0, 225), "blue": (255, 0, 0)}
confidence_threshold = 0.3

print("setting up models...")
model = YOLO("ventura-best.pt") #robot detection model
reader = easyocr.Reader(['en'], recog_network='english_g2', user_network_directory=None) #text detection model

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


print("finding robots...")
# do the detections
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
    
# find numbers
print("finding numbers...")
for robot in robots:
    x1, y1, x2, y2 = robot[4][0], robot[4][1]+5, robot[5][0], robot[5][1]+5
    searchbox = image[y1:y2, x1:x2]

    # do some processing to detect numbers better
    searchbox = cv2.cvtColor(searchbox, cv2.COLOR_BGR2GRAY)
    gaussian = cv2.GaussianBlur(searchbox, (3, 3), 0)
    searchbox = cv2.addWeighted(searchbox, 2.0, gaussian, -1.0, 0)
    searchbox = cv2.resize(searchbox, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)

    text = reader.readtext(searchbox, detail=0, allowlist="0123456789") 
    robot[6] = text
    # cv2.rectangle(frame, robot[4], robot[5], (0, 0, 225), 5)
    cv2.putText(frame, f"{robot[0]}: {robot[6]}", (x1, y1 - 5), 0, 1, (0, 0, 0), 3)


for robot in robots:
    cord = robot[1]
    point = np.array([[cord]], dtype="float32")
    if cord[1] < 644: # detections in the top full field camera
        transformed_point = cv2.perspectiveTransform(point, fullmatrix)
    else:
        if cord[0] < 959: # detections in the left field camera
            transformed_point = cv2.perspectiveTransform(point, leftmatrix)
        else: # detections in the right field camera
            transformed_point = cv2.perspectiveTransform(point, rightmatrix)
    transformed_x, transformed_y = transformed_point[0][0]
    fixed_point = (int(transformed_x), int(transformed_y))
    cv2.circle(field, fixed_point, 20, colors[robot[2]], 5)      
    cv2.putText(field, f"{robot[0]}: {robot[6]}", fixed_point, 0, 1, (0, 0, 0), round(robot[3]*5))

print("displaying results...")
cv2.imshow("ITS REAL", field)
cv2.imshow("LETS PROJECT", frame)

print("press any key to quit")
cv2.waitKey(0)
cv2.destroyAllWindows()
