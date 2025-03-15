import ast
import time
import cv2
import math
import numpy as np

with open('+output.txt', 'r') as file:
    dump = file.read()

paths = ast.literal_eval(dump)

COLORS = {"0": (0, 0, 255), "1": (0, 255, 255), "2": (0, 255, 0), "3": (255, 255, 0), "4": (255, 0, 0), "5": (255, 0, 255)}
robots = []


VISUAL = False


class Robot:
    def __init__(self, id, cord, color, number, cords, following):
        self.id = id
        self.cord = cord
        self.color = color
        self.number = number
        self.cords = cords
        self.following = following

class Path:
    def __init__(self, color, number, start, startcord, end, endcord, cords):
        self.start = start
        self.startcord = startcord
        self.end = end
        self.endcord = endcord
        self.color = color
        self.number = number
        self.cords = cords


simplified_paths = []
start_frame = 99999

end_frame = 0
print(paths[0])

for path in paths:
    c = path[4]
    #confidence check
    simplified_paths.append(Path(path[2], path[1], min(c), c[min(c)], max(c), c[max(c)], c))
    if min(c) < start_frame:
        start_frame = min(c)
    if max(c) > end_frame:
        end_frame = max(c)

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
                print(f'path added, length of {len(path.cords)}')
            elif len(robots) < 6:
                robots.append(Robot(len(robots), path.startcord, path.color, path.number, path.cords, True))
                print(f'robot created with path length of {len(path.cords)}')
            else:
                print(f"oops, i missed out on a path that was {len(path.cords)}, at {path.startcord}")
    if VISUAL:
        field = cv2.imread("/Users/colinhaine/Desktop/yolo-env/comptracker/top-down.png")

    for robot in robots:
        if frame_number in robot.cords:
            robot.cord = robot.cords[frame_number]
        elif frame_number > max(robot.cords):
            robot.following = False

        if VISUAL:
            if len(robot.cords) > 1:  
                sorted_frames = sorted(robot.cords.keys()) 
                for i in range(len(sorted_frames) - 1):
                    frame1, frame2 = sorted_frames[i], sorted_frames[i + 1]
                    cv2.line(field, robot.cords[frame1], robot.cords[frame2], COLORS[str(robot.id)], 2)
            cv2.circle(field, robot.cord, 5, COLORS[str(robot.id)], -1)
            cv2.putText(field, f"{robot.color}{robot.id}", robot.cord, 0, 1, (0, 0, 0), 3)
    if VISUAL:
        cv2.imshow('paths', field)
        if cv2.waitKey(1) == 27:
            break

    frame_number += 1
print("done!")


def smooth_path(coord_dict, window_size=5): #this function created by chatgpt
    frames = sorted(coord_dict.keys())
    smoothed_coords = {}
    for i in range(len(frames)):
        start = max(0, i - window_size // 2)
        end = min(len(frames), i + window_size // 2 + 1)
        avg_x = int(np.mean([coord_dict[frames[j]][0] for j in range(start, end)]))
        avg_y = int(np.mean([coord_dict[frames[j]][1] for j in range(start, end)]))
        smoothed_coords[frames[i]] = (avg_x, avg_y)
    return smoothed_coords

if not VISUAL:
    for robot in robots:
        robot.cords = smooth_path(robot.cords, window_size=5)
        robot.cord = robot.cords[min(robot.cords)]
    
    for f in range(start_frame, end_frame):
        field = cv2.imread("/Users/colinhaine/Desktop/yolo-env/comptracker/top-down.png")

        for robot in robots:
            if f in robot.cords:
                robot.cord = robot.cords[f]
            if len(robot.cords) > 1:  
                sorted_frames = sorted(robot.cords.keys()) 
                for i in range(len(sorted_frames) - 1):
                    frame1, frame2 = sorted_frames[i], sorted_frames[i + 1]
                    cv2.line(field, robot.cords[frame1], robot.cords[frame2], COLORS[str(robot.id)], 2)
        for robot in robots:
            cv2.circle(field, robot.cord, 10, tuple(round(c * 0.7) for c in COLORS[str(robot.id)]), -1)
            cv2.putText(field, f"{robot.color}{robot.id}", robot.cord, 0, 1, (0, 0, 0), 3)
        
        cv2.imshow('paths', field)
        time.sleep(0.033)
        if cv2.waitKey(1) == 27:
            break