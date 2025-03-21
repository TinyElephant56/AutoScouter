# Captures a twitch livestream live
# Code by someone else: https://codeberg.org/capybased/twitch-live-capture/src/branch/main/twitch-capture.py#

import os
import subprocess
import threading
import streamlink
from datetime import datetime, timedelta
import logging
import argparse
import sys
import signal
from moviepy import VideoFileClip
scriptdir = os.path.dirname(os.path.abspath(__file__))

# Argument parser setup
parser = argparse.ArgumentParser(description="Twitch Stream Capture Tool")
parser.add_argument("--log", action="store_true", help="Enable logging")
args = parser.parse_args()

# Create a logger object
logger = logging.getLogger(__name__)
logger.handlers = []  # Clear any default handlers

# If --log is specified, configure logging
if args.log:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
else:
    # Disable all logging at the root level if --log is not specified
    logging.disable(logging.CRITICAL)

# Ensure that Captures and Logs directories exist
# os.makedirs("Captures", exist_ok=True)
# os.makedirs("Logs", exist_ok=True)

# Clear the screen
print("\033[2J\033[H", end="")

with open(f"{scriptdir}/+current.txt") as file:
    key = file.read()
# Print welcome message with special formatting
# print("""\033[35m
# ___        ___  __        ___          __        __  ___       __   ___ 
#  |  |  | |  |  /  ` |__|   |  \  /    /  `  /\  |__)  |  |  | |__) |__  
#  |  |/\| |  |  \__, |  | . |   \/     \__, /~~\ |     |  \__/ |  \ |___ 

# ----not my code---\033[0m
# """)
print(f"competition: {key}")
# Prompt for streamer ID input
name = input('match name: ')
streamer_id = "firstinspires10"
# firstinspires4


# Check if the streamer_id is empty
if not streamer_id:
    print("Error: No streamer ID entered. Please provide a valid streamer ID.")
    sys.exit(1)

# Function to get the best available stream URL for a Twitch channel
def get_stream_url(channel_name):
    stream_url = f"https://www.twitch.tv/{channel_name}"
    try:
        stream_links = streamlink.streams(stream_url)
        if "best" in stream_links:
            return stream_links["best"].url
        else:
            raise ValueError("No available streams found for the channel.")
    except Exception as e:
        raise ValueError(f"Error retrieving stream for {channel_name}: {str(e)}")

# Function to calculate file size and format duration of the captured video
def calculate_video_stats(filename):
    try:
        clip = VideoFileClip(filename)
        duration_seconds = clip.duration
        duration_formatted = str(
            timedelta(seconds=int(duration_seconds))
        )  # Formatting duration
        size = os.path.getsize(filename)
        return duration_formatted, size
    except Exception as e:
        logger.error(f"Error calculating video stats: {e}")
        return "Unknown", 0

# Function to download a Twitch stream using ffmpeg and save it to a file
def download_stream(stream_url, channel_name, stop_event):
    output_filename = f"{scriptdir}/../Captures/{name}.mp4"
    log_filename = os.path.join(
        "Logs",
        datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S") + "-" + channel_name + ".log",
    )

    if args.log:
        logger.info(f"Stream URL: {stream_url}")

    if os.path.exists(output_filename):
        if args.log:
            logger.error(f"File {output_filename} already exists.")
        return

    print(f"\nCapturing stream to:\033[35m {output_filename}\033[0m\n")

    cmd = [
        "ffmpeg",
        "-i",
        stream_url,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-b:v",
        "1M",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-f",
        "mp4",
        "-y",
        output_filename,
    ]

    with subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ) as ffmpeg_process, open(log_filename, "a") if args.log else open(
        os.devnull, "w"
    ) as log_file:
        try:
            while not stop_event.is_set():
                output = ffmpeg_process.stdout.readline()
                if output == "" and ffmpeg_process.poll() is not None:
                    break
                if args.log:
                    log_file.write(output)
        except Exception as e:
            logger.error(f"Error during stream capture: {e}")
        finally:
            if ffmpeg_process.poll() is None:
                ffmpeg_process.terminate()
            ffmpeg_process.wait()

    # Calculate video statistics after ensuring ffmpeg process has terminated
    if os.path.exists(output_filename):
        duration, size = calculate_video_stats(output_filename)
        print("")
        print(
            f"Stream captured. Duration: {duration}. File size: {size / 1024 / 1024:.2f} MB."
        )
        print("")
    else:
        print("Failed to capture the stream.")

def start_capture(stop_event):
    try:
        stream_url = get_stream_url(streamer_id)
        if args.log:
            logger.info("Stream URL: {}".format(stream_url))

        capture_thread = threading.Thread(
            target=download_stream, args=(stream_url, streamer_id, stop_event)
        )
        capture_thread.start()
        return capture_thread
    except ValueError as e:
        print(e)
        return None

def signal_handler(sig, frame):
    print("Interrupt received, stopping capture...")
    stop_event.set()

def input_handler(stop_event):
    input("Press Enter to stop capturing...\n")
    stop_event.set()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        parser.print_help()
        sys.exit(0)

    stop_event = threading.Event()
    signal.signal(signal.SIGINT, signal_handler)

    capture_thread = start_capture(stop_event)

    if capture_thread:
        input_thread = threading.Thread(target=input_handler, args=(stop_event,))
        input_thread.start()

        capture_thread.join()
        input_thread.join()

    sys.exit(0)