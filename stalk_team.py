import os
import shutil
import requests
import json
from capture_video import download_yt, get_TBA
from get_increments import get_increments
from track_robots import get_paths
from select_corners import get_corners

def get_team_matches(scriptdir, team):
    print(f'jasdkfh {team}')
    with open (f'{scriptdir}/data/super-secret-API-key.txt', 'r') as file:
        token = file.read()
    headers = {"X-TBA-Auth-Key": token}
    response = requests.get(f'https://www.thebluealliance.com/api/v3/team/frc{team}/matches/2025/simple', headers=headers)
    if response.status_code == 200:
        print(response.json())

        matchdump = response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        raise Exception("Couldnt get TBA matches") 
    output = {}
    matchdump = sorted(matchdump, key=lambda x: x['actual_time'], reverse=True)[:5]
    for x in matchdump:
        output[x['actual_time']] = x['key']
    return output

if __name__ == "__main__":
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    team = 1323
    os.makedirs(f'{scriptdir}/teams/{team}', exist_ok=True)

    matches = get_team_matches(scriptdir, team)
    with open(f'{scriptdir}/teams/{team}/recentkeys.json', 'w') as file:
        json.dump(matches, file)
    print(matches)


    if True:
        for time in matches:
            key = matches[time]
            path = f"{scriptdir}/matches/{key}"
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"PURGED {key}")

    for time in matches:
        key = matches[time]
        print(f"getting the match {key}")

        event_missing = get_TBA(scriptdir, key)

        if not os.path.exists(f"{scriptdir}/matches/{key}/{key}.mp4"):
            download_yt(scriptdir, key)
            get_increments(scriptdir, key, INCREMENTS=False)

        if event_missing:
            print('you need to ge tthe corners!!')
            print(f"------{event_missing}-------{key}-----")
            get_corners(scriptdir, key, event_missing)

        if not os.path.exists(f"{scriptdir}/matches/{key}/{key}_paths.json"):
            get_paths(scriptdir, key)

