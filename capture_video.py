# downlaods youtube video from the url using yt_dlp
import yt_dlp
import os
import requests
import json

# scriptdir = os.path.dirname(os.path.abspath(__file__))

# with open (f'{scriptdir}/data/current.txt', 'r') as file:
#     key = file.read().strip()
# print(f"\033[32mAutoScout file 1 - get TBA data and download yt video\033[0m")
# print(f"\033[34m[press enter to use what is in blue]\033[0m")
# key = input(f"TBA match key:\033[34m [{key}] \033[0m") or key #look at this cool little trick!
# with open (f'{scriptdir}/data/current.txt', 'w') as file:
#     file.write(key)


def get_TBA(scriptdir, key):
    with open (f'{scriptdir}/data/super-secret-API-key.txt', 'r') as file:
        token = file.read()

    url = f'https://www.thebluealliance.com/api/v3/match/{key}'
    headers = {"X-TBA-Auth-Key": token}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()  # Parse JSON response
        formatted_data = {
            'startTime': 240,
            'url': f"https://www.youtube.com/watch?v={data['videos'][0]['key']}",
            'blue': {
                'numbers': data['alliances']['blue']['team_keys'],
                'score':data['score_breakdown']['blue']['wallAlgaeCount'],

                'netAlgaeCount': data['score_breakdown']['blue']['netAlgaeCount'],
                'wallAlgaeCount': data['score_breakdown']['blue']['wallAlgaeCount'],
                'teleopCoralCount': data['score_breakdown']['blue']['teleopCoralCount'],
                'autoCoralCount': data['score_breakdown']['blue']['autoCoralCount'],
                'foulCount': data['score_breakdown']['blue']['foulCount'],
                'autoMobilityPoints': data['score_breakdown']['blue']['autoMobilityPoints'],
                'increments': {}
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
                'increments': {}
            }
        }
        os.makedirs(f"{scriptdir}/matches/{key}", exist_ok=True)
        with open(f'{scriptdir}/matches/{key}/{key}_data.json', 'w') as file:
            json.dump(formatted_data, file)
        print(f"Successfully saved match data to \033[32m{scriptdir}/matches/{key}/{key}_data.json\033[0m")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False


def download_yt(scriptdir, key):
    # try: 
    #     with open (f'{scriptdir}/matches/{key}/{key}_data.json', 'r') as file:
    #         data = json.load(file)
    #         url = input(f"Youtube url found:\033[34m [{data['url']}] \033[0m") or data['url']

    # except:
    #     url = input(f"Enter youtube url:\033[34m [no url found] \033[0m")
    with open (f'{scriptdir}/matches/{key}/{key}_data.json', 'r') as file:
        data = json.load(file)
    url = data['url']
    print("Starting video download...")
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f"{scriptdir}/matches/{key}/{key}.mp4",
        'merge_output_format': 'mp4',
        # 'quiet': True,
        # 'no_warnings': True  
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print(f"Downloaded video to \033[32m{ydl_opts['outtmpl']}\033[0m")

