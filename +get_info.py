print('imports...')
import easyocr
import os
import cv2
import json
import requests

scriptdir = os.path.dirname(os.path.abspath(__file__))

print(f"loading detection")
cap = cv2.VideoCapture(scriptdir+"/../Captures/finals_1.mp4")
# cap.set(cv2.CAP_PROP_POS_MSEC, 8000)

reader = easyocr.Reader(['en'], recog_network='english_g2', user_network_directory=None) #text detection model

bluesearch = [(783, 67), (898, 126)]
redsearch = [(1024, 66), (1140, 126)]
timesearch = [[899, 61], [1021, 126]]

bluescore = 0
redscore = 0
blueresults = {}
redresults = {}

#--- get TBA
token = 'Fz3O8X9BRqJT8XeIs1Rcnl6rSy65NbbajU2e2V18Gc9m4vi7rG2o5QnwPUulcpz7'
url = 'https://www.thebluealliance.com/api/v3/match/2025cave_qm75'
headers = { 
    "X-TBA-Auth-Key": token
}
response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()  # Parse JSON response
    print(f"got TBA data for key: {data['event_key']}")
else:
    print(f"Error: {response.status_code} - {response.text}")


def detect_numbers(image, search):
    roi = image[search[0][1]:search[1][1], search[0][0]: search[1][0]]
    # roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(roi, detail=0, allowlist="0123456789:")
    return results
print('detecting')

started = False
while True:    
    ret, frame = cap.read()
    if not ret:
        break
    frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    
    if not started:
        h = detect_numbers(frame, timesearch)
        if h and h != ['0:00']:
            started = True
            start_frame = frame_number
            print(f"started at frame {start_frame} with {'0:00'}")

    if started and frame_number%2 == 0: #speedy
        score = detect_numbers(frame, bluesearch)
        if len(score) > 0:
            score = int(score[0])
            if score != bluescore:
                blueresults[frame_number] = score-bluescore
                print(f"blue increment of {score-bluescore} at frame {frame_number}")
                bluescore = score

        score = detect_numbers(frame, redsearch)
        if len(score) > 0:
            score = int(score[0])
            if score != redscore:
                redresults[frame_number] = score-redscore
                print(f"red increment of {score-redscore} at frame {frame_number}")
                redscore = score

formatted = {
    'key':data['key'],
    'startFrame': start_frame,
    'blue': {
        'numbers': data['blue']['team_keys'],
        'score':data['blue']['wallAlgaeCount'],

        'netAlgaeCount': data['blue']['netAlgaeCount'],
        'wallAlgaeCount': data['blue']['wallAlgaeCount'],
        'teleopCoralCount': data['blue']['teleopCoralCount'],
        'autoCoralCount': data['blue']['autoCoralCount'],
        'foulCount': data['blue']['foulCount'],

        'autoMobilityPoints': data['blue']['autoMobilityPoints'],
        'increments': blueresults
    },
    'red': {
        'numbers': data['red']['team_keys'],
        'score':data['red']['wallAlgaeCount'],

        'netAlgaeCount': data['red']['netAlgaeCount'],
        'wallAlgaeCount': data['red']['wallAlgaeCount'],
        'teleopCoralCount': data['red']['teleopCoralCount'],
        'autoCoralCount': data['red']['autoCoralCount'],
        'foulCount': data['red']['foulCount'],

        'autoMobilityPoints': data['red']['autoMobilityPoints'],
        'increments': redresults
    }
}

with open('+score_increment.json', 'w') as file:
    json.dump(redresults, file, )