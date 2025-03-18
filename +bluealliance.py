import json
import requests

token = 'Fz3O8X9BRqJT8XeIs1Rcnl6rSy65NbbajU2e2V18Gc9m4vi7rG2o5QnwPUulcpz7'
url = 'https://www.thebluealliance.com/api/v3/match/2025cave_qm75'
headers = { 
    "X-TBA-Auth-Key": token
}
response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()  # Parse JSON response
    print(data)
else:
    print(f"Error: {response.status_code} - {response.text}")

# match_data = {
#     "key": data['key'],
#     "blue": {
#         "numbers": data['alliances']['blue']['team_keys']
#         'auto-coral': 
#     },
#     "red": {
#         5: 5
#     }
# }


with open('+jsondump.json', 'w') as file:
    json.dump(data, file)