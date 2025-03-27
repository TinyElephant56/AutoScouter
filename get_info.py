print('imports...')
import easyocr
import os
import cv2
import json
import requests

scriptdir = os.path.dirname(os.path.abspath(__file__))

print(f"loading detection...")

with open(f'{scriptdir}/current.txt', 'r') as file:
    key = file.read()

cap = cv2.VideoCapture(scriptdir+f"/../Captures/{key}.mp4")
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"frames: {frame_count}, fps: {cap.get(cv2.CAP_PROP_FPS)}")
# cap.set(cv2.CAP_PROP_POS_MSEC, 8000)

reader = easyocr.Reader(['en'], recog_network='english_g2', user_network_directory=None) #text detection model

bluesearch = [(783, 67), (898, 126)]
redsearch = [(1024, 66), (1140, 126)]
timesearch = [[899, 61], [1021, 126]]
def detect_numbers(image, search):
    roi = image[search[0][1]:search[1][1], search[0][0]: search[1][0]]
    # roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(roi, detail=0, allowlist="0123456789:")
    return results

# --- get TBA info----
token = 'Fz3O8X9BRqJT8XeIs1Rcnl6rSy65NbbajU2e2V18Gc9m4vi7rG2o5QnwPUulcpz7'
url = f'https://www.thebluealliance.com/api/v3/match/{key}'
headers = { 
    "X-TBA-Auth-Key": token
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()  # Parse JSON response
    print(f"got TBA data for key {data['event_key']}")
else:
    print(f"Error: {response.status_code} - {response.text}")


bluescore = 0
redscore = 0
blueresults = {}
redresults = {}

#-----Main loop:get numbers increments from video
print('detecting...')
started = False
while True:    
    ret, frame = cap.read()
    if not ret:
        break
    frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    # print(frame_number)
    
    if not started:
        h = detect_numbers(frame, timesearch)
        if h and h != ['0:00']:
            started = True
            start_frame = frame_number
            print(f"started at frame {start_frame} with {'0:00'}")
            break

#     if started and frame_number%2 == 0: #speedy
#         score = detect_numbers(frame, bluesearch)
#         if len(score) > 0:
#             score = int(score[0])
#             if score != bluescore:
#                 blueresults[frame_number] = score-bluescore
#                 print(f"[blue {frame_number}: +{score-bluescore}]")
#                 bluescore = score

#         score = detect_numbers(frame, redsearch)
#         if len(score) > 0:
#             score = int(score[0])
#             if score != redscore:
#                 redresults[frame_number] = score-redscore
#                 print(f"[red {frame_number}: +{score-redscore}]")
#                 redscore = score

    # 'teleTime': start_frame + 480,
formatted = {
    'startTime': start_frame,
    'key':data['key'],
    'blue': {
        'numbers': data['alliances']['blue']['team_keys'],
        'score':data['score_breakdown']['blue']['wallAlgaeCount'],

        'netAlgaeCount': data['score_breakdown']['blue']['netAlgaeCount'],
        'wallAlgaeCount': data['score_breakdown']['blue']['wallAlgaeCount'],
        'teleopCoralCount': data['score_breakdown']['blue']['teleopCoralCount'],
        'autoCoralCount': data['score_breakdown']['blue']['autoCoralCount'],
        'foulCount': data['score_breakdown']['blue']['foulCount'],
        'autoMobilityPoints': data['score_breakdown']['blue']['autoMobilityPoints'],
        'increments': blueresults
    },
    'red': {
        'numbers': data['alliances']['red']['team_keys'],
        'score':data['score_breakdown']['red']['wallAlgaeCount'],

        'netAlgaeCount': data['score_breakdown']['red']['netAlgaeCount'],
        'wallAlgaeCount': data['score_breakdown']['red']['wallAlgaeCount'],
        'teleopCoralCount': data['score_breakdown']['red']['teleopCoralCount'],
        'autoCoralCount': data['score_breakdown']['red']['autoCoralCount'],
        'foulCount': data['score_breakdown']['red']['foulCount'],
        'autoMobilityPoints': data['score_breakdown']['red']['autoMobilityPoints'],
        'increments': redresults
    }
}

print(formatted)

with open(f'{data["key"]}_data.json', 'w') as file:
    json.dump(formatted, file)