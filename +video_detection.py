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
import math
from rapidfuzz import process, fuzz

cap = cv2.VideoCapture("../Captures/elims_13.mp4")
cap.set(cv2.CAP_PROP_POS_MSEC, 15000)

field_reference = cv2.imread("top-down.png")

#---toggle number detection---
TEXT_DETECTION = False
#---way faster when its off---
options = {
    "blue": ['5026', '6060', '3863'],
    "red": ['971', '4079', '589']
}
MATCH_THRESHOLD = 50



# some constants:
COLORS = {"red": (0, 0, 255), "blue": (255, 0, 0), "grey": (128, 128, 128), "dull-red": (224, 215, 215), "dull-blue": (204, 211, 237)}
CONFIDENCE_THRESHOLD = 0.4

print("setting up models...")
model = YOLO("ventura-best.pt") #robot detection model

if TEXT_DETECTION:
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

active_paths = []
archived_paths = []
path_id = 0
PATH_DRAW = True

# a pause to drag windows around:
cv2.imshow("top down view", field_reference)
ret, frame = cap.read()
cv2.imshow("video", frame)
cv2.waitKey(0)
print("detecting")

while True:    
    ret, frame = cap.read()
    if not ret:
        break

    frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    field = field_reference.copy()

    results = model(frame, device="mps", verbose=False, iou=0.8)
    result = results[0]
    bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
    confidences = np.array(result.boxes.conf.cpu())
    classes = np.array(result.boxes.cls.cpu(), dtype="int")
    detections = []
    # each item in robots is a detection.
    # [0: id, 1: center cord, 2: color, 3: confidence, 4: bbox top-left, 5: bbox bottom-right, 6: detected number, 7: type]

    id = 0
    for cls, bbox, conf in zip(classes, bboxes, confidences):
        (x1, y1, x2, y2) = bbox
        cord = (int((x1 + x2) / 2), int((y1 + y2) / 2)) #get the center of the bounding box (bbox)
        if conf > CONFIDENCE_THRESHOLD:
            if cls == 0:
                cv2.circle(frame, (int((x1+x2)/2), int((y2-y1)*0.6+y1)), 20, COLORS["blue"], 5)
                detections.append([id, cord, "blue", conf, (x1, y1), (x2, y2), "", "-"])
            elif cls == 1:
                cv2.circle(frame, (int((x1+x2)/2), int((y2-y1)*0.6+y1)), 20, COLORS["red"], 5)
                detections.append([id, cord, "red", conf, (x1, y1), (x2, y2), "", "-"])
        id += 1
    
    if TEXT_DETECTION:
        for i in range(len(detections)):
            x1, y1, x2, y2 = detections[i][4][0], detections[i][4][1]+5, detections[i][5][0], detections[i][5][1]+5
            searchbox = frame[y1:y2, x1:x2]

            # do some processing to detect numbers better
            searchbox = cv2.cvtColor(searchbox, cv2.COLOR_BGR2GRAY)
            gaussian = cv2.GaussianBlur(searchbox, (3, 3), 0)
            searchbox = cv2.addWeighted(searchbox, 2.0, gaussian, -1.0, 0)
            searchbox = cv2.resize(searchbox, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)

            text = reader.readtext(searchbox, detail=0, allowlist="0123456789") 
            #it tries to fuzz, but its really bad at reading the numbers right now
            if text:
                text = max(text, key=len)
                fuzzed = process.extractOne(text, options[detections[i][2]], scorer=fuzz.ratio)
                if fuzzed[1] > MATCH_THRESHOLD:
                    print(fuzzed[0])
                    detections[i][6] = "!"+ str(fuzzed[0])
                else:
                    detections[i][6] = "X" + text
            cv2.putText(frame, f"{detections[i][6]}", (x1, y1 - 5), 0, 1, (255, 255, 255), 3)
        
    #turn the coordinate into the top down view
    for i in range(len(detections)):
        cord = detections[i][1]
        point = np.array([[cord]], dtype="float32")
        if cord[1] < 644:  # detections in the top full field camera
            transformed_x, transformed_y = map(int, cv2.perspectiveTransform(point, fullmatrix)[0][0])
            detections[i][1] = (transformed_x, transformed_y)
            detections[i][7] = "top"
        else:
            if cord[0] < 959:  # detections in the left field camera
                transformed_x, transformed_y = map(int, cv2.perspectiveTransform(point, leftmatrix)[0][0])
                detections[i][1] = (transformed_x, transformed_y)
                detections[i][7] = "side"
            else:  # detections in the right field camera
                transformed_x, transformed_y = map(int, cv2.perspectiveTransform(point, rightmatrix)[0][0])
                detections[i][1] = (transformed_x, transformed_y)
                detections[i][7] = "side"
    
    #--- graph it ---
    for detection in detections:
        if detection[7] == "top":
            cv2.circle(field, detection[1], 20, COLORS["dull-"+detection[2]], 3)   
        else:
            cv2.circle(field, detection[1], 20, COLORS["dull-"+detection[2]], -1)   
        cv2.putText(field, f"{detection[6]}", detection[1], 0, 1, (0, 0, 0), round(detection[3] * 5))
    
    #--- d is cleaned up distance ---
    d = detections.copy() 
    while len(d) >= 2:
        shortest = 80 #try to beat this distance
        best_pair = None
        for i in d:
            for j in d:
                if i[2] == j[2] and i[7] != 'midpoint' and j[7] != 'midpoint' and i[7] != j[7]:
                    dist = math.dist(i[1], j[1])
                    if dist < shortest:
                        shortest = dist
                        best_pair = (i, j)
        if best_pair:
            i, j = best_pair
            midpoint = ((i[1][0] + j[1][0]) // 2, (i[1][1] + j[1][1]) // 2)
            d.append([(i[0] * 100 + j[0]), midpoint, i[2], (i[3] + j[3]), i[4], i[5], i[6], 'midpoint'])

            for k in d[:]:
                if math.dist(midpoint, k[1]) < 60 and k[7] != 'midpoint':
                    d.remove(k)
        else:
            break
    i = 0
    while i < len(d) - 1:
        j = i + 1
        while j < len(d):
            if math.dist(d[i][1], d[j][1]) < 40:
                d.pop(j) 
            else:
                j += 1  
        i += 1  
    
    # --- graph the cleaned up robot positions---
    for robot in d:
        cv2.circle(field, robot[1], 10, COLORS[robot[2]], -1)

    # --- path detecting goes here ---
    #path: [0:id, 1:init_frame, 2: color, 3: conf, 4:list of cords and times]
    for path in archived_paths:
        past = path[4]
        color = path[2]
        if len(past) > 1:
            for i in range(len(past)-1):
                cv2.line(field, past[i][1], past[i+1][1], COLORS["dull-"+color], 2)
        
    for path in active_paths[:]:
        past = path[4]
        last_frame = past[-1][0]
        last_cord = past[-1][1]
        color = path[2]
        closest = 100
        best_robot = None
        for robot in d:
            if math.dist(last_cord, robot[1]) < closest and color == robot[2]:
                best_robot = robot
        
        if best_robot:
            past += [[frame_number, best_robot[1]]]
            d.remove(best_robot)
            active_paths[active_paths.index(path)][4] = past
        else:
            if frame_number - last_frame > 5:
                archived_paths.append(path)
                active_paths.remove(path)
                
        #draw it
        if len(past) > 1:
            for i in range(len(past)-1):
                cv2.line(field, past[i][1], past[i+1][1], COLORS[color], 2)

    for robot in d: #initialize a path for any left over ones
        active_paths.append([path_id, frame_number, robot[2], robot[3], [ [frame_number,robot[1]] ] ])
        path_id += 1

    # --- graph the corners ---
    for corners in [fullframecorners, leftframecorners, rightframecorners]:
        for corner in corners:
            cv2.circle(frame, (corner[0], corner[1]), 10, (0, 255, 0), -1)
    for corners in [fullfieldcorners, leftfieldcorners, rightfieldcorners]:
        for corner in corners:
            cv2.circle(field, (corner[0], corner[1]), 10, (0, 255, 0), -1)

    cv2.circle(field, (300, 300), 40, COLORS["grey"], 2)
    cv2.imshow("top down view", field)
    cv2.imshow("video", frame)

    if cv2.waitKey(1) == 27:
        break
    #code for frame by frame stepper
    # key = cv2.waitKey(0)
    # if key == 27:
    #     break
archived_paths += active_paths


print(detections)
print("stopped.")
cap.release()
cv2.destroyAllWindows()
