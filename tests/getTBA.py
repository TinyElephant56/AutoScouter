print('imports...')
import os
import cv2
import json
import requests

# --- get TBA info----
token = 'Fz3O8X9BRqJT8XeIs1Rcnl6rSy65NbbajU2e2V18Gc9m4vi7rG2o5QnwPUulcpz7'
url = f'https://www.thebluealliance.com/api/v3/event/2025azgl/matches/keys'
headers = { 
    "X-TBA-Auth-Key": token
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()  # Parse JSON response
    # with open("++hajsdf.json", 'w') as file:
    #     json.dump(data, file)
    print(data)
else:
    print(f"Error: {response.status_code} - {response.text}")

