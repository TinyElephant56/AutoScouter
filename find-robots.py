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
with open (f'{scriptdir}/data/current.txt', 'r') as file:
    key = file.read().strip()
print(f"\033[32mAutoScout file 2 - AI track match video\033[0m")
key = input(f"Match key:\033[34m [{key}] \033[0m") or key #look at this cool little trick!
with open (f'{scriptdir}/data/current.txt', 'w') as file:
    file.write(key)

with open (f'{scriptdir}/matches/{key}/{key}_data.json') as file:
    data = json.load(file)

cap = cv2.VideoCapture(f"{scriptdir}/matches/{key}/{key}.mp4")
cap.set(cv2.CAP_PROP_POS_FRAMES, data['startTime'])

field_reference = cv2.imread(f"{scriptdir}/data/top-down.png")

options = {
    "blue": [x[3:] for x in data['blue']['numbers']],
    "red": [x[3:] for x in data['red']['numbers']]
}

print(options)
MATCH_THRESHOLD = 50

GROUP_DISTANCE = 90

# some constants:
COLORS = {"red": (0, 0, 255), "blue": (255, 0, 0), "grey": (128, 128, 128), "dull-red": (204, 211, 237), "dull-blue": (224, 215, 215)}
CONFIDENCE_THRESHOLD = 0.4

print("setting up models...")
model = YOLO(scriptdir+"/data/ventura-best-2.pt") #robot detection model

reader = easyocr.Reader(['en'], recog_network='english_g2', user_network_directory=None) #text detection model

allcorners = json.load(open(f"{scriptdir}/data/fieldcorners.json", 'r'))
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
PAUSE = False
STEPTHROUGH = False
# a pause to drag windows around:

def get_numbers(bbox1, bbox2): ## OLD NOT UPDATED FOR DETECTION OBJECT
        x1, y1 = bbox1
        x2, y2 = bbox2
        searchbox = frame[y1:y2, x1:x2]

        # do some processing to detect numbers better
        searchbox = cv2.cvtColor(searchbox, cv2.COLOR_BGR2GRAY)
        gaussian = cv2.GaussianBlur(searchbox, (3, 3), 0)
        searchbox = cv2.addWeighted(searchbox, 2.0, gaussian, -1.0, 0)
        searchbox = cv2.resize(searchbox, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)

        text = reader.readtext(searchbox, detail=0, allowlist="0123456789") 
        return text
        

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

class Path:
    def __init__(self, init_time, last_time, color, last_cord, cords):
        self.init_time = init_time
        self.last_time = last_time
        self.color = color
        self.last_cord = last_cord
        self.cords = cords

        self.number = None

    def __str__(self):
        return str([0, self.init_time, self.color, self.number, self.cords], )
        #path: [0:id, 1:init_frame, 2: color, 3: conf, 4:list of cords and times]

        
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
    cv2.rectangle(frame, [403, 370], [511, 394], (0,0,0), -1)

    frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    field = field_reference.copy()

    results = model(frame, device="mps", verbose=False, iou=0.8)
    result = results[0]
    bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
    confidences = np.array(result.boxes.conf.cpu())
    classes = np.array(result.boxes.cls.cpu(), dtype="int")
    detections = []

    id = 0
    for cls, bbox, conf in zip(classes, bboxes, confidences):
        (x1, y1, x2, y2) = bbox
        cord = (int((x1 + x2) / 2), int((y1 + y2) / 2)) #get the center of the bounding box (bbox)
        if conf > CONFIDENCE_THRESHOLD:
            if cls == 0:
                # cv2.circle(frame, (int((x1+x2)/2), int((y2-y1)*0.6+y1)), 20, COLORS["blue"], 5)
                detections.append(Detection(id, cord, "blue", conf, (x1, y1), (x2, y2), "", "-"))
            elif cls == 1:
                # cv2.circle(frame, (int((x1+x2)/2), int((y2-y1)*0.6+y1)), 20, COLORS["red"], 5)
                detections.append(Detection(id, cord, "red", conf, (x1, y1), (x2, y2), "", "-"))
        id += 1
    

    for detection in detections:
        cv2.rectangle(frame, detection.bbox1, detection.bbox2, COLORS[detection.color], 3, 1)
        cord = detection.cord
        point = np.array([[cord]], dtype="float32")
        if cord[1] < 644:  # detections in the top full field camera
            transformed_x, transformed_y = map(int, cv2.perspectiveTransform(point, fullmatrix)[0][0])
            detection.type = "top"
        else:
            if cord[0] < 959:  # detections in the left field camera
                transformed_x, transformed_y = map(int, cv2.perspectiveTransform(point, leftmatrix)[0][0])
                detection.type = "side"
            else:  # detections in the right field camera
                transformed_x, transformed_y = map(int, cv2.perspectiveTransform(point, rightmatrix)[0][0])
                detection.type = "side"
        detection.cord = (transformed_x, transformed_y)
    
    #--- graph it ---
    for detection in detections:
        if detection.type == "top":
            cv2.circle(field, detection.cord, 20, COLORS["dull-"+detection.color], 3)   
        else:
            cv2.circle(field, detection.cord, 20, COLORS["dull-"+detection.color], -1)   
    
    d = detections.copy() 
    # remove duplicate detections
    i = 0
    while i < len(d) - 1:
        j = i + 1
        while j < len(d):
            if math.dist(d[i].cord, d[j].cord) < 40 and d[i].type == d[j].type:
                if d[i].conf < d[j].conf:
                    d.pop(i)
                    i -= 1  
                    break 
                else:
                    d.pop(j)  
            else:
                j += 1  
        i += 1  

    #--- match up pairs of detections from different angles ---
    while len(d) >= 2:
        shortest = GROUP_DISTANCE #try to beat this distance
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
                if math.dist(midpoint, k.cord) < shortest+1 and k.type != 'midpoint' and k.color == i.color:
                    d.remove(k)
        else:
            break
    
    
    # --- graph the cleaned up robot positions---
    for robot in d:
        cv2.circle(field, robot.cord, 10, COLORS[robot.color], -1)

    # --- path detecting goes here ---
    #make an list of how close every pair combination is
    distances = []
    for detection in d:
        for path in active_paths:
            distance = math.dist(path.last_cord, detection.cord)
            if distance < 150 and path.color == detection.color: #<- here
                distances.append((distance, detection, path))
    distances = sorted(distances, key=lambda x: x[0])

    
    for distance, detection, path in distances:
        if detection in d and path in active_paths and frame_number not in path.cords:
            path.cords[frame_number] = detection.cord
            path.last_cord = detection.cord
            path.last_time = frame_number

            if len(path.cords)%20 == 5 and not path.number:
                text = get_numbers(detection.bbox1, detection.bbox2)
                if text:
                    text = max(text, key=len)
                    fuzzed = process.extractOne(text, options[detection.color], scorer=fuzz.ratio)
                    if fuzzed[1] > 70:
                        path.number = fuzzed[0]
                    #     print(fuzzed[0])
                    # else:
                    #     print(f"{detection.color} {text}, looks most like {fuzzed[0]}, conf {fuzzed[1]}")
                # cv2.rectangle(frame, detection.bbox1, detection.bbox2, COLORS[detection.color], 3, 1)

            d.remove(detection)

    for path in active_paths:
        #kill off old paths
        if frame_number - path.last_time > min(12, len(path.cords)+1):
            archived_paths.append(path)
            active_paths.remove(path)
            
        
    for detection in d: #start new paths
        active_paths.append(Path(frame_number, frame_number, detection.color, detection.cord, { frame_number:detection.cord } ))
    
    for path in archived_paths:
        if len(path.cords) > 1:  # Ensure there are at least two points
            sorted_frames = sorted(path.cords.keys())  # Sort the frame numbers
            for i in range(len(sorted_frames) - 1):
                frame1, frame2 = sorted_frames[i], sorted_frames[i + 1]
                cv2.line(field, path.cords[frame1], path.cords[frame2], COLORS["dull-"+path.color], 2)
    
    for path in active_paths:
        if len(path.cords) > 1:  # Ensure there are at least two points
            sorted_frames = sorted(path.cords.keys())  # Sort the frame numbers
            for i in range(len(sorted_frames) - 1):
                frame1, frame2 = sorted_frames[i], sorted_frames[i + 1]
                cv2.line(field, path.cords[frame1], path.cords[frame2], COLORS[path.color], 2)
        cv2.circle(field, path.last_cord, 10, (0, 0, 0), 2)
        if path.number:
            cv2.putText(field, f"{path.number}", path.last_cord, 0, 1, (0, 0, 0), 3)


    # --- graph the corners ---
    for corners in [fullframecorners, leftframecorners, rightframecorners]:
        for corner in corners:
            cv2.circle(frame, (corner[0], corner[1]), 10, (0, 255, 0), -1)
    for corners in [fullfieldcorners, leftfieldcorners, rightfieldcorners]:
        for corner in corners:
            cv2.circle(field, (corner[0], corner[1]), 10, (0, 255, 0), -1)

    cv2.imshow("top down view", field)
    cv2.imshow("video", frame)

    
    if cv2.waitKey(1) == 27:
         break
cap.release()
cv2.destroyAllWindows()

archived_paths += active_paths
output = '['
for path in archived_paths:
    output += str(path)+", "
output += ']'

# if input("save paths to +output.txt? [y/n]") == 'y':
with open (f'{scriptdir}/matches/{key}/{key}_paths.txt', 'w') as file:
    file.write(output)
print(f"stopped at{frame_number}")
print(f"Saved paths to \033[32m{scriptdir}/matches/{key}/{key}_paths.txt\033[0m")


