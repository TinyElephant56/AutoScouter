# Autoscout
by Colin Haine, March 2025

## Description
the goal is to be able to fully scout a FRC match, to get each of the robot's paths and to determine which robot scored

a work in progress.
detects robots from an image with a YOLOv8 model.
trained specifically on cave2025.
uses easyocr to look for the numbers on the bumpers.

run +detectionwithtext.py
or +video_detection after downloading the video from elims 13 from stream-youtube.py

ai robot detection model dataset:
https://universe.roboflow.com/frcrobotfinder/ventura-2025 

## Next steps
more or less in order of what i'll work on
- location the position of all six robots
    - find clumps of two points, each point is a different angles
- ✅ impliment video- its actually pretty fast!
    - find the optimal arrangement for the corners so that the detections overlap best
    - ✅ see if number detection greatly lowers speed it does- about 3x slower with what i have
- add tracking:
    - in the past i just got the closest new detection to a robot in the last frame to use as the new position
    - with bumper number detection we can be more observant to ensure that the robots don't switch
    - if we can get paths, we can determine velocity. the predicted spot can be a third coordinate to be used when determining robot coordinates
    - a path display
- improve bumper number accuracy with better filters
- add scoring:
    - have it read the time and numbers in the top display.
    - you can detect around the time someone scores when the time increments. 
    - also read the team numbers from the top or use bluealliance api, i think reading the numbers what i'll do
    - you can match digits more or less to narrow down the bumper detection to be accurate
- add an interface:
    - automatically get a video, from twitch or youtube
    - crop down that video to the standard size that i used (so we don't have to get new corners every time)
    - maybe a discord bot interface (because its easiest for backend)
    - get a server or computer to run it. right now its very slow (my goal rn is accuracy, i'll work on reducing the model later) 
    - a web interface to view results?
- do some robot detection accuracy tests to see how viable this whole project is...

## Installation
uses python 3.10, beacause thats what ultralytics wants

install requirements.txt
```sh
pip install -r requirements.txt
```
if i forgot something or you need the corerct version, look in requirements-dump.txt.  it has some really random stuff lmao.

i did it in a venv (i keep forgetting how to start it so i put the code here)
```sh
python3 -m venv yolo-env
source yolo-env/bin/activate
```

if you have any questions dont be afraid to ask
