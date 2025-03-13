# Autoscout
by Colin Haine, March 2025

## Description
the goal is to be able to fully scout a FRC match, to get each of the robot's full paths with perfect accuracy and to determine when each robot scores
a work in progress

### How it works
1: ai detects the robots in every frame using YOLOv8 model
2: perspective transform the points onto the map
3: clump points together
4: form a list of smaller paths
4.5-partially done: use bumper numbers to determine the confidence in each path (easyocr)
5-not done: stitch the paths together into one big one for each robot

ai robot detection model dataset, trained specifically on cave2025:
https://universe.roboflow.com/frcrobotfinder/ventura-2025 

### Run it
- run +video_detection.py
- right now, its set up to use the video from elims 13 cave.
- you can get a youtube stream using stream-youtube.py
- you can get new corner values with select-corners.py, and paste them into fieldcorners.json

### Next steps
more or less in order of what i'll work on
- ✅ location the position of all six robots
    - ✅ find clumps of two points, each point is a different angles
    - use confidence values.
- ✅ impliment video- its actually pretty fast!
    - ✅ find the optimal arrangement for the corners so that the detections overlap best- needs to be adjusted occasionally
    - ✅ see if number detection greatly lowers speed it does- about 3x slower with what i have
- ✅ add tracking:
    - ✅ in the past i just got the closest new detection to a robot in the last frame to use as the new position
    - with bumper number detection we can be more observant to ensure that the robots don't switch
    - add confidence values to each path

- * make the detections represented by an object, not just raw values in an array *
- improve bumper number accuracy with better filters
- add scoring:
    - have it read the time and numbers in the top display.
    - you can detect around the time someone scores when the time increments. 
    - also read the team numbers from the top or use bluealliance api, i think reading the numbers what i'll do
    - ✅ you can match digits more or less to narrow down the bumper detection to be accurate- good enoughish?
- add an interface:
    - ✅ automatically get a video, from twitch or youtube
    - crop down that video to the standard size that i used (so we don't have to get new corners every time)
    - maybe a discord bot interface (because its easiest for backend)
    - get a server or computer to run it. right now its very slow (my goal rn is accuracy, i'll work on reducing the model later) 
    - a web interface to view results?

## Installation
uses python 3.10, beacause thats what ultralytics wants

install the poetry file

i did it in a venv (i keep forgetting how to start it so i put the code here)
```sh
python3 -m venv yolo-env
source yolo-env/bin/activate
```

if you have any questions dont be afraid to ask
