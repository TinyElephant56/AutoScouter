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
import time
import os

scriptdir = os.path.dirname(os.path.abspath(__file__))
print(f"{scriptdir}")

cap = cv2.VideoCapture(scriptdir+"/../Captures/elims_2.mp4")
cap.set(cv2.CAP_PROP_POS_MSEC, 8000)

field_reference = cv2.imread(scriptdir+"/top-down.png")

#---toggle number detection---
TEXT_DETECTION = False
#---way faster when its off---
options = {
    "blue": ['5026', '6060', '3863'],
    "red": ['971', '4079', '589']
}
MATCH_THRESHOLD = 50

# some constants:
COLORS = {"red": (0, 0, 255), "blue": (255, 0, 0), "grey": (128, 128, 128), "dull-red": (204, 211, 237), "dull-blue": (224, 215, 215)}
CONFIDENCE_THRESHOLD = 0.4

print("setting up models...")
model = YOLO(scriptdir+"/ventura-best-2.pt") #robot detection model

if TEXT_DETECTION:
    reader = easyocr.Reader(['en'], recog_network='english_g2', user_network_directory=None) #text detection model

allcorners = json.load(open(scriptdir+"/fieldcorners.json", 'r'))
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

frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

active_paths = []
archived_paths = []
path_id = 0
PATH_DRAW = True
PAUSE = True
STEPTHROUGH = False
# a pause to drag windows around:

class Detection:
    def __init__(self, id, cord, color, conf, bbox1, bbox2, number, type):
        self.id = id
        self.cord = cord
        self.color = color
        self.conf = conf
        self.bbox1 = bbox1
        self.bbox2 = bbox2
        self.number = number
        self.type = type

if PAUSE:
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
                detections.append(Detection(id, cord, "blue", conf, (x1, y1), (x2, y2), "", "-"))
            elif cls == 1:
                cv2.circle(frame, (int((x1+x2)/2), int((y2-y1)*0.6+y1)), 20, COLORS["red"], 5)
                detections.append(Detection(id, cord, "red", conf, (x1, y1), (x2, y2), "", "-"))
        id += 1
    
    if TEXT_DETECTION: ## OLD NOT UPDATED FOR DETECTION OBJECT
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
        cord = detections[i].cord
        point = np.array([[cord]], dtype="float32")
        if cord[1] < 644:  # detections in the top full field camera
            transformed_x, transformed_y = map(int, cv2.perspectiveTransform(point, fullmatrix)[0][0])
            detections[i].type = "top"
        else:
            if cord[0] < 959:  # detections in the left field camera
                transformed_x, transformed_y = map(int, cv2.perspectiveTransform(point, leftmatrix)[0][0])
                detections[i].type = "side"
            else:  # detections in the right field camera
                transformed_x, transformed_y = map(int, cv2.perspectiveTransform(point, rightmatrix)[0][0])
                detections[i].type = "side"
        detections[i].cord = (transformed_x, transformed_y)
    
    #--- graph it ---
    for detection in detections:
        if detection.type == "top":
            cv2.circle(field, detection.cord, 20, COLORS["dull-"+detection.color], 3)   
        else:
            cv2.circle(field, detection.cord, 20, COLORS["dull-"+detection.color], -1)   
        cv2.putText(field, f"{detection.number}", detection.cord, 0, 1, (0, 0, 0), round(detection.conf * 5))
    
    #--- d is cleaned up distance ---
    d = detections.copy() 
    while len(d) >= 2:
        shortest = 80 #try to beat this distance
        best_pair = None
        for i in d:
            for j in d:
                if i.color == j.color and i.type != 'midpoint' and j.type != 'midpoint' and i.type != j.type:
                    dist = math.dist(i.cord, j.cord)
                    if dist < shortest:
                        shortest = dist
                        best_pair = (i, j)
        if best_pair:
            i, j = best_pair
            midpoint = ((i.cord[0]+j.cord[0]) // 2, (i.cord[1]+j.cord[1]) // 2)
            d.append(Detection((i.id * 100 + j.id), midpoint, i.color, (i.conf + j.conf), i.bbox1, i.bbox2, i.number, 'midpoint'))

            for k in d[:]:
                if math.dist(midpoint, k.cord) < 80 and k.type != 'midpoint' and k.color == i.color:
                    d.remove(k)
        else:
            break
    i = 0
    while i < len(d) - 1:
        j = i + 1
        while j < len(d):
            if math.dist(d[i].cord, d[j].cord) < 40:
                if d[i].conf < d[j].conf:
                    d.pop(i)  # Remove the lower-confidence detection
                    i -= 1  # Step back to recheck the new d[i]
                    break  # Restart checking from the current i
                else:
                    d.pop(j)  # Remove d[j] since it has lower confidence
            else:
                j += 1  
        i += 1  
    
    # --- graph the cleaned up robot positions---
    for robot in d:
        cv2.circle(field, robot.cord, 10, COLORS[robot.color], -1)

    # --- path detecting goes here ---
    #path: [0:id, 1:init_frame, 2: color, 3: conf, 4:list of cords and times]
    for path in archived_paths:
        past = path[4]
        color = path[2]
        if len(past) > 1:  # Ensure there are at least two points
            sorted_frames = sorted(past.keys())  # Sort the frame numbers
            for i in range(len(sorted_frames) - 1):
                frame1, frame2 = sorted_frames[i], sorted_frames[i + 1]
                cv2.line(field, past[frame1], past[frame2], COLORS["dull-"+color], 2)
        
    for path in active_paths[:]:
        color = path[2]
        confidence = path[3]
        past = path[4]
        last_frame = max(past)
        last_cord = past[max(past)]
        
        closest = 100
        best_robot = None
        for robot in d:
            if math.dist(last_cord, robot.cord) < closest and color == robot.color:
                best_robot = robot
        
        if best_robot:
            best_cord = best_robot.cord
            past[frame_number] = best_cord
            confidence += best_robot.conf
            d.remove(best_robot)
            active_paths[active_paths.index(path)][3] = confidence
            active_paths[active_paths.index(path)][4] = past
        elif frame_number - last_frame > 8: # <- here
            archived_paths.append(path)
            active_paths.remove(path)
        if len(past) > 1:  
            sorted_frames = sorted(past.keys()) 
            for i in range(len(sorted_frames) - 1):
                frame1, frame2 = sorted_frames[i], sorted_frames[i + 1]
                cv2.line(field, past[frame1], past[frame2], COLORS[color], 2)

    for robot in d: #start new paths
        active_paths.append([path_id, frame_number, robot.color, robot.conf, { frame_number:robot.cord } ])
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
print("stopped.")
cap.release()
cv2.destroyAllWindows()

# chill_one_second = input('frigging packet')
# --- clean up false positives ---
archived_paths += active_paths
for path in archived_paths[:]:
    confidence = path[3]
    if path[3] < 3: #if the path is about 1, 2, or 3 frames kill it 
        archived_paths.remove(path)
with open ('+output.txt', 'w') as file:
    file.write(str(archived_paths))
print(frame_number)

# chill_one_second = input('frigging packet')
# #--- second track ---
# robots = []
# #robot [0:id, 1:(recentcord), 2: color 3: number 4: paths]
# frame = 0
# for frame in range(frame_count):
#     for path in archived_paths:
#         if path[1] == frame:
#             print(f'initialized! at frame {frame}')
#     time.sleep(0.0333)