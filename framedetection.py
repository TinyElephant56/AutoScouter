# only detects robots from an image. go to +detectionwithtext.py

import json
import requests
import cv2
from ultralytics import YOLO
import numpy as np

frame = cv2.imread("frame_36.jpg")

model = YOLO("ventura-best.pt")

allcorners = json.load(open(f"fieldcorners.json", 'r'))

fullfieldcorners = allcorners["fullfieldcorners"]
leftfieldcorners = allcorners["leftfieldcorners"]
rightfieldcorners = allcorners["rightfieldcorners"]

fullframecorners = allcorners["fullframecorners"]
leftframecorners = allcorners["leftframecorners"]
rightframecorners = allcorners["rightframecorners"]

field = cv2.imread("field.png")

fullmatrix = cv2.getPerspectiveTransform(np.array(fullframecorners, dtype="float32"), np.array(fullfieldcorners, dtype="float32"))
leftmatrix = cv2.getPerspectiveTransform(np.array(leftframecorners, dtype="float32"), np.array(leftfieldcorners, dtype="float32"))
rightmatrix = cv2.getPerspectiveTransform(np.array(rightframecorners, dtype="float32"), np.array(rightfieldcorners, dtype="float32"))


results = model(frame, device="mps", verbose=False, iou=0.8)
result = results[0]
bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
confidences = np.array(result.boxes.conf.cpu())
classes = np.array(result.boxes.cls.cpu(), dtype="int")
robots = []

confidence_threshold = 0.3

id = 0
for cls, bbox, conf in zip(classes, bboxes, confidences):
    (x1, y1, x2, y2) = bbox
    cord = (int((x1 + x2) / 2), int((y1 + y2) / 2))
    if conf > confidence_threshold:
        cv2.putText(frame, f"{id}", (x1, y1 - 5), 0, 1, (255, 255, 255), 3)
        # cv2.putText(frame, f"{id}: {conf*100:.0f}%", (x1, y1 - 5), 0, 1, (255, 255, 255), 3)

        if cls == 0:
            cv2.circle(frame, (int((x1+x2)/2), int((y2-y1)*0.6+y1)), 20, (255, 0, 0), 5)
            robots.append([id, cord, "blue", conf])
        elif cls == 1:
            cv2.circle(frame, (int((x1+x2)/2), int((y2-y1)*0.6+y1)), 20, (0, 0, 255), 5)
            # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 225), 5)
            robots.append([id, cord, "red", conf])
    id += 1

i = 0
for robot in robots:
    cord = robot[1]
    point = np.array([[cord]], dtype="float32")
    if cord[1] < 644:
        transformed_point = cv2.perspectiveTransform(point, fullmatrix)
        transformed_x, transformed_y = transformed_point[0][0]
        fixed_point = (int(transformed_x), int(transformed_y))

        if robot[2] == "red":
            cv2.circle(field, fixed_point, 20, (0, 0, 255), 5)
        else:
            cv2.circle(field, fixed_point, 20, (255, 0, 0), 5)

        cv2.putText(field, f"{i}", fixed_point, 0, 1, (255, 255, 255), 2)
    else:
        if cord[0] < 959:
            transformed_point = cv2.perspectiveTransform(point, leftmatrix)
            transformed_x, transformed_y = transformed_point[0][0]
            fixed_point = (int(transformed_x), int(transformed_y))

            if robot[2] == "red":
                cv2.circle(field, fixed_point, 20, (0, 0, 255), 5)
            else:
                cv2.circle(field, fixed_point, 20, (255, 0, 0), 5) 

            cv2.putText(field, f"{i}", fixed_point, 0, 1, (255, 255, 255), 5)
        else:
            transformed_point = cv2.perspectiveTransform(point, rightmatrix)
            transformed_x, transformed_y = transformed_point[0][0]
            fixed_point = (int(transformed_x), int(transformed_y))
            
            if robot[2] == "red":
                cv2.circle(field, fixed_point, 20, (0, 0, 255), 5)
            else:
                cv2.circle(field, fixed_point, 20, (255, 0, 0), 5) 
                           
            cv2.putText(field, f"{i}", fixed_point, 0, 1, (255, 255, 255), 5)
    i += 1

for corners in [fullframecorners, leftframecorners, rightframecorners]:
    for corner in corners:
        cv2.circle(frame, (corner[0], corner[1]), 10, (0, 255, 0), -1)

for corners in [fullfieldcorners, leftfieldcorners, rightfieldcorners]:
    for corner in corners:
        cv2.circle(field, (corner[0], corner[1]), 10, (0, 255, 0), -1)
    

cv2.imshow("ITS REAL", field)
cv2.imshow("LETS PROJECT", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
