import ast
import time
import cv2
import math
import numpy as np
import os
import json
import requests
import csv
from path import Path
        
def merge_paths(scriptdir, key, LIVE=False, VISUAL=False, VIDEO=False, log_func=None):
    class Robot:
        def __init__(self, id, cord, color, number, cords, following):
            self.id = id
            self.cord = cord
            self.color = color
            self.number = number
            self.cords = cords
            self.following = following

            self.scoring = None
            self.intaking = None
            self.coral = 1
            self.movement = []
            self.cycles = 0

    class ScoringInstance:
        def __init__(self, time, coral_conf, d_conf, m_conf, score_conf, color):
            self.time = time
            self.coral_conf = coral_conf #how likely robot is to have coral
            self.d_conf = d_conf
            self.m_conf = m_conf
            self.score_conf = score_conf
            self.color = color
        def get_total_conf(self):
            return self.coral_conf * self.d_conf * self.m_conf * self.score_conf
        def __str__(self):
            return f"{self.color}{self.time}: {round(self.coral_conf, 2)}|{round(self.d_conf, 2)}|{round(self.m_conf)}|{round(self.score_conf)}"

    class IntakeIntance:
        def __init__(self, time, d_conf, m_conf, color):
            self.time = time
            self.d_conf = d_conf
            self.m_conf = m_conf

    with open(f'{scriptdir}/matches/{key}/{key}_data.json', 'r') as file:
        matchdata = json.load(file)
    
    with open(f"{scriptdir}/matches/{key}/{key}_paths.json", "r") as file:
        pathdata = json.load(file)
        paths = [Path.from_dict(item) for item in pathdata]

    print(len(paths))

    COLORS = {"0": (255, 255, 0), "1": (0, 255, 255), "2": (0, 127, 255), "3": (0, 0, 255), "4": (255, 0, 0), "5": (255, 0, 255)}
    robots = []
    FOLLOW_DISTANCE = 200

    start_frame = matchdata['startTime']
    end_frame = start_frame+3600
    frame_number = start_frame

    paths = list(filter(lambda path: len(path.cords) >= 10, paths)) #majestic lambda function by chatgpt
    missed_paths = []

    #---------preprocess----------
    while frame_number < end_frame:
        #if the path started on the frame, add it to the closest robot
        for path in paths:
            if path.init_time == frame_number:
                closest = FOLLOW_DISTANCE
                bestrobot = None
                for robot in robots:
                    if not robot.following and robot.color == path.color:
                        if math.dist(robot.cord, path.init_cord) < closest:
                            bestrobot = robot
                if bestrobot:
                    bestrobot.cords.update(path.cords) #add dict to dict
                    if not bestrobot.number:
                        bestrobot.number = path.number
                    bestrobot.following = True
                elif len(robots) < 6:
                    robots.append(Robot(len(robots), path.init_cord, path.color, path.number, path.cords, True))
                else:
                    # print(f"missed {path.color} length {len(path.cords)}")
                    # if path.number:
                        missed_paths.append(path)
        
        for path in missed_paths[:]:
            closest = FOLLOW_DISTANCE
            bestrobot = None
            for robot in robots:
                if not robot.following and robot.color == path.color:
                    if math.dist(robot.cord, path.init_cord) < closest:
                        bestrobot = robot
            if bestrobot:
                bestrobot.cords.update(path.cords) #add dict to dict
                if not bestrobot.number:
                        bestrobot.number = path.number
                bestrobot.following = True

                missed_paths.remove(path)
                # print(f'rejoined with {bestrobot.id}')

        
        if LIVE:
            field = cv2.imread(f"{scriptdir}/data/top-down.png")
        
        for robot in robots:
            if frame_number in robot.cords:
                robot.cord = robot.cords[frame_number]
            elif frame_number > int(max(robot.cords)):
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
            for path in missed_paths:
                if len(path.cords) >1:
                    sorted_frames = sorted(path.cords.keys())
                    for i in range(len(sorted_frames) - 1):
                        frame1, frame2 = sorted_frames[i], sorted_frames[i + 1]
                        cv2.line(field, path.cords[frame1], path.cords[frame2], (200, 200, 200), 2)
            cv2.imshow('paths', field)
            if cv2.waitKey(1) == 27:
                LIVE = False

        frame_number += 1
    cv2.destroyAllWindows()
    for path in missed_paths:
        print(f'lost {path.color} length {len(path.cords)}')
    if log_func: 
        log_func('merged paths, generating output video')
    
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

    def map_value(x):
        return max(0.5, min(1, 1 - (x - 100) / 100))

    def map_value2(x):
        return 1 if x > 30 else 1 + (30 - x) / 30

    def map_value3(x):
        return max(0.5, min(1, 1 - (x - 150) / 150))

    def draw_text_list(image, text_list, position=(10, -10), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=1, color=(0, 0, 0), thickness=2, line_spacing=30):
        h, w, _ = image.shape
        x, y = position
        y = h + y if y < 0 else y
        for i, text in enumerate(reversed(text_list)):  # Reverse to stack bottom-up
            text_y = y - (i * line_spacing)
            cv2.putText(image, f"{text_list[text]}", (x, text_y), font, font_scale, color, thickness)

    def draw_text_list_bottom_right(image, text_list, position=(-10, -10), font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=1, color=(0, 0, 0), thickness=2, line_spacing=30):
        h, w, _ = image.shape
        x, y = position
        x = w + x if x < 0 else x  # Adjust x for right alignment
        y = h + y if y < 0 else y  # Adjust y for bottom alignment
        
        for i, text in enumerate(reversed(text_list)):  # Reverse to stack bottom-up
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = x - text_size[0]  # Align text to the right
            text_y = y - (i * line_spacing)
            cv2.putText(image, text, (text_x, text_y), font, font_scale, color, thickness)

    def put_text_top_right(image, text, font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=1, color=(0, 0, 0), thickness=2):
        cv2.putText(image, str(text), (image.shape[1] - cv2.getTextSize(str(text), font, font_scale, thickness)[0][0] - 10, cv2.getTextSize(str(text), font, font_scale, thickness)[0][1] + 10), font, font_scale, color, thickness)

    def put_text_top_left(image, text, font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=1, color=(0, 0, 0), thickness=2):
        cv2.putText(image, str(text), (10, cv2.getTextSize(str(text), font, font_scale, thickness)[0][1] + 10), font, font_scale, color, thickness)

    def linear_distance(cord1, cord2):
        return abs(cord1[0]-cord2[0]) + abs(cord2[1]- cord2[1])


    #-------Main function------
    cap = cv2.VideoCapture(f"{scriptdir}/matches/{key}/{key}.mp4")
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_number = start_frame

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    field_ref = cv2.imread(f"{scriptdir}/data/top-down.png")
    field_width = field_ref.shape[1]
    field_height = field_ref.shape[0]

    new_video_height = int(height * (field_width / width))
    output_size = (field_width, new_video_height + field_height)

    #setup
    for robot in robots: 
        robot.cords = smooth_path(robot.cords, window_size=5)
        robot.cord = robot.cords[min(robot.cords)]
    scorings = {}
    intakes = {}
    increments = []

    fieldelements = {
        "blue": {
            "reef":(348, 318),
            "source1":(20, 0),
            "source2":(20, 632)
        },
        "red": {
            "reef":(1029, 320),
            "source1":(1360, 0),
            "source2":(1360, 632)
        }
    }
    print('creating output video')

    if VIDEO:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4
        out = cv2.VideoWriter(f"{scriptdir}/matches/{key}/{key}_final.mp4", fourcc, fps, output_size)
    start_frame = matchdata['startTime']
    end_frame = start_frame + 3600
    length = end_frame-start_frame
    step_size = length // 50 #every 2 percent
    frame_number = start_frame

    start_time = time.time()
    while frame_number < end_frame:
        if VISUAL or VIDEO: 
            ret, video = cap.read()
            if not ret:
                break
            field = field_ref.copy()

        for robot in robots:
            if frame_number in robot.cords:
                robot.cord = robot.cords[frame_number]

            #calculate distance to reef
            reef_dist = math.dist(robot.cord, fieldelements[robot.color]['reef'])
            if robot.scoring:
                if reef_dist < 200: #distane to leave
                    if map_value(reef_dist) > scorings[robot.scoring].d_conf:
                        scorings[robot.scoring].d_conf = map_value(reef_dist)
                        scorings[robot.scoring].time = frame_number
                    # cv2.circle(field, robot.cord, int(map_value(reef_dist)*20), (0, 0, 0), 2)
                else:
                    robot.scoring = None
            elif reef_dist < 140: #inidiate a new one
                if robot.coral > 0.5:
                    scoringid = len(scorings)+1
                    robot.scoring = scoringid
                    scorings[scoringid] = ScoringInstance(frame_number, coral_conf=robot.coral, d_conf=0.5, m_conf=1, score_conf=1, color=robot.color)
                    
                    robot.cycles += 1
                    robot.coral = 0

            #calculate distance to source
            source_dist = min(linear_distance(robot.cord, fieldelements[robot.color]['source1']), linear_distance(robot.cord, fieldelements[robot.color]['source2']))
            if robot.intaking:
                if source_dist < 180:
                    if map_value3(source_dist) > intakes[robot.intaking].d_conf:
                        intakes[robot.intaking].d_conf = map_value3(source_dist)
                        intakes[robot.intaking].time = frame_number
                        robot.coral = map_value3(source_dist)
                    # cv2.circle(field, robot.cord, int(map_value(source_dist)*20), (0, 0, 0), 2)
                else:
                    robot.intaking = None
            elif source_dist < 170:
                intakingid = len(intakes)
                robot.intaking = intakingid
                intakes[intakingid] = IntakeIntance(frame_number, d_conf=map_value3(source_dist), m_conf=1, color=robot.color)

            #calculate movement
            if frame_number-1 in robot.cords:
                robot.movement.append(math.dist(robot.cord, robot.cords[frame_number-1]))
                if len(robot.movement) > 15:
                    robot.movement.pop(0)
            recent_movement = map_value2(sum(robot.movement))
            if robot.scoring:
                if recent_movement > scorings[robot.scoring].m_conf:
                    scorings[robot.scoring].m_conf = recent_movement

            if VISUAL or VIDEO:
                if len(robot.cords) > 1:  
                    sorted_frames = sorted(robot.cords.keys()) 
                    for i in range(len(sorted_frames) - 1):
                        if sorted_frames[i] < frame_number: #now it looks cool
                            frame1, frame2 = sorted_frames[i], sorted_frames[i + 1]
                            cv2.line(field, robot.cords[frame1], robot.cords[frame2], COLORS[str(robot.id)], 2)
                
                # if robot.intaking:
                #     cv2.putText(field, f"{round(intakes[robot.intaking].d_conf, 2)}", robot.cord, 0, 1, (0, 0, 0), 3)
                # if robot.scoring:
                #     cv2.putText(field, f"{round(scorings[robot.scoring].get_total_conf(), 2)}", robot.cord, 0, 1, (0, 0, 0), 3)
                    # f"{round(scorings[robot.scoring].get_total_conf(), 2)}"
        
        for color in ['blue', 'red']:
            if str(frame_number) in matchdata[color]['increments']:
                increments.append(frame_number)
                print(frame_number)
        
        frame_number += 1

        if VISUAL or VIDEO:
            for robot in robots:
                cv2.circle(field, robot.cord, 20, tuple(round(c * 0.6) for c in COLORS[str(robot.id)]), -1)
                cv2.putText(field, f"{robot.number} | {robot.cycles}", robot.cord, 0, 1, (0, 0, 0), 3)

            draw_text_list(field, scorings)
            draw_text_list_bottom_right(field, increments)
            put_text_top_right(field, str(frame_number))
            put_text_top_left(field, f"{key}")

        if (frame_number-start_frame) % step_size == 0:
            percent = ((frame_number-start_frame) / length) * 100
            elapsed_time = time.time() - start_time
            average_speed = elapsed_time / (frame_number-start_frame)
            remaining_steps = length - (frame_number-start_frame)
            eta = remaining_steps * average_speed
            
            if log_func:
                log_func(f"{key}: {percent:.0f}% done, ETA {eta:.1f}s\n")
            else:
                print(f"{key}: {percent:.0f}% done, ETA {eta:.1f}s\n")

        if VIDEO:
            field_width = field.shape[1]
            video_resized = cv2.resize(video, (field_width, int(video.shape[0] * (field_width / video.shape[1]))))
            combined_frame = np.vstack((video_resized, field))
            out.write(combined_frame)

        if VISUAL:
            cv2.imshow('Replay', combined_frame)
            if cv2.waitKey(1) == 27:
                VISUAL=False
                print('skipping')

       
    if VIDEO or VISUAL:
        cap.release()
        cv2.destroyAllWindows()

    if VIDEO:
        out.release()
    

    print(f"writing to {scriptdir}/matches/{key}/{key}_cycles.csv")
    with open(f"{scriptdir}/matches/{key}/{key}_cycles.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["match", "team", "cycles"])  # Header row
        
        for robot in robots:
            writer.writerow([key, robot.number, robot.cycles])
            if log_func:
                log_func(f"{key} {robot.number} {robot.cycles}")

if __name__ == "__main__":
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    with open (f'{scriptdir}/data/current.txt', 'r') as file:
        key = file.read().strip()
    merge_paths(scriptdir, key, VIDEO=True)