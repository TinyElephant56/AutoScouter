import ast
import time
import cv2
import math
import numpy as np
import os
import json
import requests

with open('+output.txt', 'r') as file:
    dump = file.read()
paths = ast.literal_eval(dump)

COLORS = {"0": (0, 0, 255), "1": (0, 255, 255), "2": (0, 255, 0), "3": (255, 255, 0), "4": (255, 0, 0), "5": (255, 0, 255)}
robots = []

# if live is True then the paths will be jagged and it will follow the robots in real time
# if live is False then it will smooth the paths and be playing a replay of the robots paths
# ------------------
LIVE = False
# ------------------

# using classes so the code looks really clean
class Robot:
    def __init__(self, id, cord, color, number, cords, following):
        self.id = id
        self.cord = cord
        self.color = color
        self.number = number
        self.cords = cords
        self.following = following

        self.scoring = None
        self.coral = 1
        self.movement = []


class Path:
    def __init__(self, color, number, start, startcord, end, endcord, cords):
        self.start = start
        self.startcord = startcord
        self.end = end
        self.endcord = endcord
        self.color = color
        self.number = number
        self.cords = cords

class ScoringInstance:
    def __init__(self, time, coral_conf, distance_conf, m_conf, score_conf):
        self.time = time
        self.coral_conf = coral_conf #how likely robot is to have coral
        self.distance_conf = distance_conf
        self.m_conf = m_conf
        self.score_conf = score_conf
        
        # self._total_conf = coral_conf * distance_conf * m_conf * score_conf
    def get_total_conf(self):
        return self.coral_conf * self.distance_conf * self.m_conf * self.score_conf

with open('scoreincrement.json', 'r') as file:
    increments = json.load(file)


#--- get end frame of the paths
simplified_paths = []
start_frame = 99999
end_frame = 0

for path in paths:
    c = path[4]
    if len(c) > 5:
        simplified_paths.append(Path(path[2], path[1], min(c), c[min(c)], max(c), c[max(c)], c))
        if min(c) < start_frame:
            start_frame = min(c)
        if max(c) > end_frame:
            end_frame = max(c)

#---------preprocess----------
frame_number = start_frame
while frame_number < end_frame:
    for path in simplified_paths:
        if path.start == frame_number:
            closest = 200
            bestrobot = None
            for robot in robots:
                if not robot.following and robot.color == path.color:
                    if math.dist(robot.cord, path.startcord) < closest:
                        bestrobot = robot
            if bestrobot:
                bestrobot.cords.update(path.cords) #add dict to dict
                bestrobot.following = True
                # print(f'path added, length of {len(path.cords)}')
            elif len(robots) < 6:
                robots.append(Robot(len(robots), path.startcord, path.color, path.number, path.cords, True))
                # print(f'robot created with path length of {len(path.cords)}')
            else:
                print(f"oops, i missed out on a path that was {len(path.cords)}, at {path.startcord}")
    if LIVE:
        field = cv2.imread("/Users/colinhaine/Desktop/yolo-env/comptracker/top-down.png")
    for robot in robots:
        if frame_number in robot.cords:
            robot.cord = robot.cords[frame_number]
        elif frame_number > max(robot.cords):
            robot.following = False
        if LIVE:
            if len(robot.cords) > 1:  
                sorted_frames = sorted(robot.cords.keys()) 
                for i in range(len(sorted_frames) - 1):
                    frame1, frame2 = sorted_frames[i], sorted_frames[i + 1]
                    cv2.line(field, robot.cords[frame1], robot.cords[frame2], COLORS[str(robot.id)], 2)
            cv2.circle(field, robot.cord, 5, COLORS[str(robot.id)], -1)
            cv2.putText(field, f"{robot.color}{robot.id}", robot.cord, 0, 1, (0, 0, 0), 3)
    if LIVE:
        cv2.imshow('paths', field)
        if cv2.waitKey(1) == 27:
            break
    frame_number += 1
print("done!")


#functions created by chatgpt:
def smooth_path(coord_dict, window_size=5): 
    frames = sorted(coord_dict.keys())
    smoothed_coords = {}
    for i in range(len(frames)):
        start = max(0, i - window_size // 2)
        end = min(len(frames), i + window_size // 2 + 1)
        avg_x = int(np.mean([coord_dict[frames[j]][0] for j in range(start, end)]))
        avg_y = int(np.mean([coord_dict[frames[j]][1] for j in range(start, end)]))
        smoothed_coords[frames[i]] = (avg_x, avg_y)
    return smoothed_coords

def map_value(x): #
    return max(0.5, min(1, 1 - (x - 100) / 100))

def map_value2(x):
    return 1 if x > 30 else 1 + (30 - x) / 30

#-------Main function------
scriptdir = os.path.dirname(os.path.abspath(__file__))
cap = cv2.VideoCapture(scriptdir+"/../Captures/finals_1.mp4")
cap.set(cv2.CAP_PROP_POS_MSEC, 8000)

#setup
for robot in robots: 
    robot.cords = smooth_path(robot.cords, window_size=5)
    robot.cord = robot.cords[min(robot.cords)]
scorings = {}

while True:    
    ret, video = cap.read()
    if not ret:
        break
    frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

    field = cv2.imread("/Users/colinhaine/Desktop/yolo-env/comptracker/top-down.png")
    cv2.circle(field, (348, 318), 150, (0,0,0), 1) #help out with visuals
    for robot in robots:
        if frame_number in robot.cords:
            robot.cord = robot.cords[frame_number]
        
        distance = math.dist(robot.cord, (348, 318))

        #calculate distance
        if robot.scoring:
            if distance < 150: #update with a higher if
                if map_value(distance) > scorings[robot.scoring].distance_conf:
                    scorings[robot.scoring].distance_conf = map_value(distance)
                    scorings[robot.scoring].time = frame_number
                #tuple(round(c * 0.6) for c in COLORS[str(robot.id)])
                cv2.circle(field, robot.cord, int(map_value(distance)*20), (0, 0, 0), 2)
            else:
                robot.scoring = None
        elif distance < 150: #inidiate a new one
            if robot.scoring == None:
                scoringid = len(scorings)+1
                robot.scoring = scoringid
                scorings[scoringid] = ScoringInstance(frame_number, coral_conf=robot.coral, distance_conf=0.5, m_conf=1, score_conf=1)
                print('scored?')

        #calculate movement
        if frame_number-1 in robot.cords:
            robot.movement.append(math.dist(robot.cord, robot.cords[frame_number-1]))
            if len(robot.movement) > 10:
                robot.movement.pop(0)
        recent_movement = map_value2(sum(robot.movement))
        if robot.scoring:
            if recent_movement > scorings[robot.scoring].m_conf:
                scorings[robot.scoring].m_conf = recent_movement

        #make the paths
        if len(robot.cords) > 1:  
            sorted_frames = sorted(robot.cords.keys()) 
            for i in range(len(sorted_frames) - 1):
                frame1, frame2 = sorted_frames[i], sorted_frames[i + 1]
                cv2.line(field, robot.cords[frame1], robot.cords[frame2], COLORS[str(robot.id)], 2)
    
    for robot in robots:
        cv2.circle(field, robot.cord, 10, tuple(round(c * 0.6) for c in COLORS[str(robot.id)]), -1)
        if robot.scoring:
            cv2.putText(field, f"{round(scorings[robot.scoring].get_total_conf(), 2)}", robot.cord, 0, 1, (0, 0, 0), 3)
    
    cv2.imshow('video', video)
    cv2.imshow('paths', field)
    if cv2.waitKey(1) == 27:
        break