print('imports...')
import easyocr
import os
import cv2
import json
import requests
def get_increments(scriptdir, key, log_func=print, INCREMENTS=True):
    cap = cv2.VideoCapture(f"{scriptdir}/matches/{key}/{key}.mp4")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    log_func(f"frames: {frame_count}, fps: {cap.get(cv2.CAP_PROP_FPS)}")
    reader = easyocr.Reader(['en'], recog_network='english_g2', user_network_directory=None) #text detection model
    with open (f'{scriptdir}/matches/{key}/{key}_data.json', 'r') as file:
        data = json.load(file)
        
    bluesearch = [(783, 67), (898, 126)]
    redsearch = [(1024, 66), (1140, 126)]
    timesearch = [[899, 61], [1021, 126]]

    def detect_numbers(image, search):
        roi = image[search[0][1]:search[1][1], search[0][0]: search[1][0]]
        # roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        results = reader.readtext(roi, detail=0, allowlist="0123456789:")
        return results

    bluescore = 0
    redscore = 0
    blueresults = {}
    redresults = {}

    log_func('getting start and end times')
    started = False
    while True:    
        ret, frame = cap.read()
        if not ret:
            break
        frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if frame_number % 10 == 0:
            h = detect_numbers(frame, timesearch)
            print(h)
            if not started:
                if h and h == ['0:14']:
                    started = True
                    start_frame = frame_number
                    print('started')
            else:
                if h and h == ['2:14']:
                    stop_frame = frame_number
                    print('ended')
                    break
        
        if started and INCREMENTS and frame_number%2 == 0:
            score = detect_numbers(frame, bluesearch)
            if len(score) > 0:
                score = int(score[0])
                if score != bluescore:
                    blueresults[frame_number] = score-bluescore
                    print(f"[blue {frame_number}: +{score-bluescore}]")
                    bluescore = score

            score = detect_numbers(frame, redsearch)
            if len(score) > 0:
                score = int(score[0])
                if score != redscore:
                    redresults[frame_number] = score-redscore
                    print(f"[red {frame_number}: +{score-redscore}]")
                    redscore = score

    data['startFrame'] = start_frame
    data['stopFrame'] = stop_frame
    with open (f'{scriptdir}/matches/{key}/{key}_data.json', 'w') as file:
        json.dump(data, file)
    log_func(f'auto start time: {start_frame}, auto end time: {stop_frame}')
    log_func(f'dumped to {scriptdir}/matches/{key}/{key}_data.json')

if __name__ == "__main__":
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    print(f"loading detection...")
    with open(f'{scriptdir}/data/current.txt', 'r') as file:
        key = file.read()

    get_increments(scriptdir, key, INCREMENTS=False)