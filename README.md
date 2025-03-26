# Autoscout
by Colin Haine, March 2025

## Description
From a video of a match, it autonomously forms the paths of each robot and how many cycles each robot does.

### What it does
get_info.py
- 0: Get TBA data api and youtube video (yt_dlp)
video_detection.py
- 1: the ai detects the robots in every frame using YOLOv8
- 2: combine the camera angles and plot detections as points on a top-down map
- 3: clumps points together and remove false positives
- 4: create paths from points that are close to points in the last frame
- 4.5: read bumper numbers every once in a while using easyocr
cleanup.py
- 5: stitch the paths together into the full march for each robot
- 6: count how many cycles each robot
  
ai robot detection model dataset, trained specifically on cave2025:
https://universe.roboflow.com/frcrobotfinder/ventura-2025 

### Next steps
- add scoring:
    - ✅ find the increments in score with the top display.
    - match up the increments and make a scoring interface
- add an interface:
    - ✅ automatically get a video, from twitch or youtube
    - crop down that video to the standard size that i used
    - start with discord bot interface (because its easiest for backend)
    - get a computer (cad laptop) or server to run it
    - a web interface view results?
- Create a database of the results
- Train a new, faster ai model
- Create documentation on how to install this

## Installation
1. Install python:
    1. Mac: Brew install python@3.10
    2. Windows: Get python
2. Install git
    1. Mac: Brew install git
    2. Windows: get from git-scm.com
3. Create a venv
4. Install poetry
    1. Mac: Brew install poetry
    2. Windows: curl -sSL https://install.python-poetry.org | python3 -
5. Clone the project
    1. Git clone https://github.com/TinyElephant56/AutoScouter
6. Test it
    1. first, get the youtube video, which downloads to a dir outside of comptracker, ../Captures/
    2. run video_detection.py
7. On a computer with GPU, install cuda drivers
    1. Windows: pain.
    2. Mac: mpu is great
