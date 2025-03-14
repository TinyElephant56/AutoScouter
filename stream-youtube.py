# downlaods youtube video from the url using yt_dlp

import yt_dlp
import random
import os

scriptdir = os.path.dirname(os.path.abspath(__file__))

url = input("youtube url: ")

def download_youtube_video(youtube_url, output_path="video.mp4"):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
        print(f"Downloaded video to {output_path}")

download_youtube_video(url, f'{scriptdir}/../Captures/{random.randint(0, 999999)}.mp4')
