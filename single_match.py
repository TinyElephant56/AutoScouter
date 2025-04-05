import os
import json
import os.path
import sys

from capture_video import get_TBA, download_yt
from track_robots import get_paths
from generate_results import merge_paths


def main():
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    
    with open (f'{scriptdir}/data/current.txt', 'r') as file:
        key = file.read().strip()
    print(f"\033[32mAutoScout- get TBA data and download yt video\033[0m")
    print(f"\033[34m[press enter to use what is in blue]\033[0m")
    key = input(f"TBA match key:\033[34m [{key}] \033[0m") or key 
    with open (f'{scriptdir}/data/current.txt', 'w') as file:
        file.write(key)
    
    if not os.path.exists(f"{scriptdir}/matches/{key}/{key}_data.json"):
        get_TBA(scriptdir, key)

    if not os.path.exists(f"{scriptdir}/matches/{key}/{key}.mp4"):
        download_yt(scriptdir, key)

    if os.path.exists(f"{scriptdir}/matches/{key}/{key}_paths.json"):
        tracked = 'n'
    else:
        tracked = 'y'
    if input(f'start tracking? [y/n]\033[34m [{tracked}] \033[0m') or tracked == 'y':
        get_paths(scriptdir, key)
    
    if input('display paths? [y/n] ') == 'y':
        merge_paths(scriptdir, key)

if __name__ == "__main__":
    main()