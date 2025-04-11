# Autoscout
by Colin Haine, April 2025

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
- MAKE IT RELIABLE
    - Correct certain maching algorithms
    - fine tune the joining points
    - handle endgame
    - use match numbers to determine confidence when matching up paths
- Add robustness for multiple competitions:
    - have a folder for each comp, that has the data for the corner locations
    - train an ai based on general lighting, add a parameter to choose which model
    - try out more models
- ADD SCORING
    - implement scoring increments
    - handle algae
- Add speed parameters (ex. skipping every other frame)
    - See how much the reliability drops if so
    - Add checkboxes/drop downs to the ui for parameters
- add tests (useful when installing on another computer since there are so many libraries used)
    - chatgpt should do a good job of this
- try installing on windows and resolve problems
    - create steps to use nvidia GPU
- raise an army to train the ai during worlds
- make the kittens cuter
- add status box for gpu utilized  

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
