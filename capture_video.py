# downlaods youtube video from the url using yt_dlp
import yt_dlp
import os
import requests
import json
import sys
import tkinter as tk

def get_TBA(scriptdir, key):
    with open (f'{scriptdir}/data/super-secret-API-key.txt', 'r') as file:
        token = file.read()

    url = f'https://www.thebluealliance.com/api/v3/match/{key}'
    headers = {"X-TBA-Auth-Key": token}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()  # Parse JSON response
        formatted_data = {
            'url': f"https://www.youtube.com/watch?v={data['videos'][0]['key']}",
            'comp': data['event_key'],
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
        if os.path.exists(f"{scriptdir}/events/{data['event_key']}.json"):
            return None
        else:
            return data['event_key']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        raise Exception("invalid key")
    

def download_yt(scriptdir, key, log_func=print):
    def hook(d): 
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '').strip()
            speed = d.get('_speed_str', '').strip()
            eta = d.get('_eta_str', '').strip()
            log_func(f"{key}: {percent} at {speed}, ETA {eta}\n")
        elif d['status'] == 'finished':
            log_func(f"{key}: Download complete.\n")

    class MyLogger:
        def debug(self, msg):
            log_func(msg)
        def warning(self, msg):
            log_func(f"WARNING: {msg}")
        def error(self, msg):
            log_func(f"ERROR: {msg}")

    with open (f'{scriptdir}/matches/{key}/{key}_data.json', 'r') as file:
        data = json.load(file)
    url = data['url']
    print("Starting video download...")
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f"{scriptdir}/matches/{key}/{key}.mp4",
        'merge_output_format': 'mp4',
        'logger': MyLogger(),
        'progress_hooks': [hook],
        'no_color': True
        # 'quiet': True,
        # 'no_warnings': True  
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print(f"Downloaded video to \033[32m{ydl_opts['outtmpl']}\033[0m")
