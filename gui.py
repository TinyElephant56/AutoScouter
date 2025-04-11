import os
import time
import shutil
import threading
import tkinter as tk
from tkinter import Toplevel, Listbox, Button
import requests
from capture_video import get_TBA, download_yt
from track_robots import get_paths
from generate_results import merge_paths
from sheets_upload import upload_to_sheets
from get_increments import get_increments
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import queue
from abc import ABC, abstractmethod
import subprocess
import csv 

scriptdir = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_QUEUE = f"{scriptdir}/processor/downloadqueue"
TRACK_QUEUE = f"{scriptdir}/processor/trackqueue"
PROCESS_QUEUE = f"{scriptdir}/processor/processqueue"
COMPLETED = f"{scriptdir}/processor/completed"

# make sure that the directories exist.
# they'll be filled will empty text files that are named the same as a folder in /matches, with the match data
for folder in [DOWNLOAD_QUEUE, TRACK_QUEUE, PROCESS_QUEUE, COMPLETED]:
    os.makedirs(folder, exist_ok=True)


# monitors a directory to detect when something is modified
class FileHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor

    def on_created(self, event):
        if not event.is_directory:
            print('something changed')
            app.update_listboxes()
            self.processor.add_to_queue(event.src_path)

# we create three of these: to download the match, do the tracking, and postprocessing
class FileProcessor(threading.Thread, ABC):
    def __init__(self, source, destination, status_callback, log_box, cat=None):
        super().__init__(daemon=True)
        self.observer = Observer() 
        self.source = source # column that it gets from
        self.destination = destination # column that it moves matches to once processed
        self.running = False
        self.queue = queue.Queue() #using a Queue so it could be expanded witout edge cases
        self.status_callback = status_callback # function to update status
        self.log_box = log_box # where it logs % complete
        self.cat = cat

    def add_to_queue(self, path):
        self.queue.put(path)

    def append_to_logbox(self, message):
        self.log_box.delete(1.0, tk.END) #you could remove this line for a long log
        self.log_box.insert(tk.END, message)
        self.log_box.yview(tk.END)

    def toggle_monitoring(self):
        if not self.running: #turn it on
            self.running = True
            if self.cat:
                self.cat.state = "active_0"
                self.cat.display()
            for file in os.listdir(self.source): #create a queue of matches
                file_path = os.path.join(self.source, file)
                if os.path.isfile(file_path):
                    self.queue.put(file_path)
            if not self.observer.is_alive(): #only create the observer the first time starting it
                event_handler = FileHandler(self)
                self.observer.schedule(event_handler, self.source, recursive=False)
                self.observer.start()
                self.start()
            self.status_callback('activated', 'green')
        else:
            self.running = False # pause it- but lets the current task finish
            self.status_callback('pausing...', 'red')
    
    def run(self):
        try:
            while True:
                if self.running:
                    if not self.queue.empty(): #process the queue
                        if self.cat: self.cat.state = "active_0"
                        file_path = self.queue.get()
                        self.process_file(file_path)
                    else:
                        self.status_callback('queue empty', 'green')
                        if self.cat: self.cat.state="idle"
                elif not self.running:
                    self.status_callback('not active', 'grey')
                    if self.cat: self.cat.state = "asleep"
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    @abstractmethod # abstract method just to impress Ms Wade
    def process_file(self, file_path): 
        pass

# first step in the pipeline: get the video and TBA data
class MatchDownloader(FileProcessor):
    def process_file(self, file_path): # polymorphism i think? (to impress Ms Wade)
        file_name = os.path.basename(file_path)

        self.status_callback(f'{file_name}: getting TBA', 'orange')
        get_TBA(scriptdir, file_name) # function in capture_video.py

        self.status_callback(f'{file_name}: getting video', 'orange')
        download_yt(scriptdir, file_name, log_func=self.append_to_logbox) # function in capture_video.py

        self.status_callback(f'{file_name}: getting start/end times', 'orange')
        get_increments(scriptdir, file_name, INCREMENTS=False, log_func=self.append_to_logbox)

        self.status_callback(f'{file_name}: success', 'green')
        new_path = os.path.join(self.destination, file_name)

        time.sleep(0.1)
        print(os.listdir(DOWNLOAD_QUEUE))
        shutil.move(file_path, new_path) # move the match in the pipeline
        app.update_listboxes() # update visually

# second part of the pipeline: runs the ai on the video
class MatchTracker(FileProcessor):
    def process_file(self, file_path):
        print('processing!')
        file_name = os.path.basename(file_path)
        self.status_callback(f'{file_name}: tracking', 'orange')
        
        # function in track_robots.py
        get_paths(scriptdir, file_name, VISUAL=False, log_func=self.append_to_logbox)
        
        new_path = os.path.join(self.destination, file_name)
        shutil.move(file_path, new_path)
        self.status_callback(f'{file_name}: done', 'green')
        app.update_listboxes()

# third part of the pipeline: forms the paths into a complete match and gets cycles
class Postprocessor(FileProcessor):
    def __init__(self, source, destination, status_callback, log_box, cat): #all this to initialize with one more variable 
        super().__init__(source, destination, status_callback, log_box, cat)
        self.visual = True 
        # visual: True  forms an output video (takes longer)
        # visual: False  just gets cycles (takes almost no time)

    def process_file(self, file_path):
        print(f'visual: {self.visual}')
        file_name = os.path.basename(file_path)

        if self.visual:
            self.status_callback(f'{file_name}: getting paths', 'orange')
        if self.visual:
            self.status_callback(f'{file_name}: forming match video', 'orange')
        
        #function in generate_results.py
        merge_paths(scriptdir, file_name, VIDEO=self.visual, log_func=self.append_to_logbox)

        new_path = os.path.join(self.destination, file_name)
        shutil.move(file_path, new_path)
        self.status_callback(f'{file_name}: done', 'green')
        app.update_listboxes()

class Cat:
    def __init__(self, frame, kind, state, column):
        self.frame = frame
        self.kind = kind
        self.state = state
        self.column = column
        self.images = {
            'asleep': tk.PhotoImage(file=f"{scriptdir}/kittens/{kind}_asleep.png").zoom(2, 2),
            'idle': tk.PhotoImage(file=f"{scriptdir}/kittens/{kind}_idle.png").zoom(2, 2),
            'active_1': tk.PhotoImage(file=f"{scriptdir}/kittens/{kind}_active_1.png").zoom(2, 2),
            'active_0': tk.PhotoImage(file=f"{scriptdir}/kittens/{kind}_active_0.png").zoom(2, 2)
        }
    def breathe(self):
        self.display()
        if self.state == "active_0":
            self.state = 'active_1'
        elif self.state == "active_1":
            self.state='active_0'

    def display(self):
        self.frame.config(image=self.images[self.state])
        self.frame.grid(row=0, column=self.column)


# main gui
class MainPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoSCout!!!") # how exciting
        self.listed_matches = None
        self.entry = None
    
        self.columns = [DOWNLOAD_QUEUE, TRACK_QUEUE, PROCESS_QUEUE, COMPLETED]
        self.listboxes = []

        # create the four columns of matches
        # each column coresponds to /downloadqueue, /processqueue, /trackqueue, or /completed
        for i in range(4):
            frame = tk.Frame(root)
            frame.grid(row=2, column=i, padx=10, pady=10)
            listbox = tk.Listbox(frame, height=15, width=30, selectmode=tk.EXTENDED)
            listbox.pack()
            self.listboxes.append(listbox)

        # the colorful statuses at the top
        self.download_status = tk.Label(root, text="Downloader not running", bg="gray", fg="white", width=30, height=2)
        self.download_status.grid(row=1, column=0, pady=10)
        self.track_status = tk.Label(root, text="Tracker not running", bg="gray", fg="white", width=30, height=2)
        self.track_status.grid(row=1, column=1, pady=10)
        self.postprocess_status = tk.Label(root, text="Postprocessor not running", bg="gray", fg="white", width=30, height=2)
        self.postprocess_status.grid(row=1, column=2, pady=10)
        tk.Label(root, text="Completed matches", bg="gray", fg="white", width=30, height=2).grid(row=1, column=3, pady=10)
        
        self.download_cat = Cat(tk.Label(root, image=None), 'download_cat', 'asleep', 0)
        self.track_cat = Cat(tk.Label(root, image=None), 'track_cat', 'asleep', 1)
        self.process_cat = Cat(tk.Label(root, image=None), 'process_cat', 'asleep', 2)
        

        # the logs at the bottom
        self.download_log = tk.Text(root, height=10, width=38)
        self.download_log.grid(row=5, column=0, pady=10)
        self.track_log = tk.Text(root, height=10, width=38)
        self.track_log.grid(row=5, column=1, pady=10)
        self.postprocess_log = tk.Text(root, height=10, width=38)
        self.postprocess_log.grid(row=5, column=2, pady=10)
        self.system_status = tk.Text(root, height=10, width=38)
        self.system_status.grid(row=5, column=3, pady=10)

        
        # creates a grid inside a grid so four buttons occupy one root grid space
        button_box0 = tk.Frame(root, pady=5) 
        button_box0.grid(row=4, column=0)
        tk.Button(button_box0, text="Add Matches", command=self.open_match_selection).grid(row=1, column=0, pady=5)
        tk.Button(button_box0, text="Clear Queue", command=self.clear_queue).grid(row=1, column=1, pady=5)
        tk.Button(button_box0, text="Start", command=self.toggle_download_daemon).grid(row=0, column=0, pady=5)
        tk.Button(button_box0, text="Refresh Files", command=self.update_listboxes).grid(row=0, column=1)
        
        button_box1 = tk.Frame(root, pady=5)
        button_box1.grid(row=4, column=1)
        tk.Button(button_box1, text="Start robot tracker", command=self.start_track_daemon).grid(row=0, column=0, pady=5)
        tk.Button(button_box1, text="Ben Mode", command=self.ben_mode).grid(row=1, column=0)

        button_box2 = tk.Frame(root, pady=5)
        button_box2.grid(row=4, column=2)
        tk.Button(button_box2, text="Get video and cycles", command=self.start_visualprocessor).grid(row=0, column=0, pady=5)
        tk.Button(button_box2, text="Get cycles", command=self.start_fastprocessor).grid(row=1, column=0, pady=5)

        button_box3 = tk.Frame(root, pady=5)
        button_box3.grid(row=4, column=3)
        tk.Button(button_box3, text="View selected match", command=self.open_selected_video).grid(row=0, column=0, columnspan=2, pady=5)
        tk.Button(button_box3, text="Quit", command=quit).grid(row=1, column=0, pady=5)
        tk.Button(button_box3, text="Upload selected", command=self.upload_results).grid(row=1, column=1, pady=5)

        

        self.update_listboxes() # visually update the columns
        # create the three daemons
        self.download_monitor = MatchDownloader(DOWNLOAD_QUEUE, TRACK_QUEUE, self.update_download_status, self.download_log, cat=self.download_cat)
        self.track_monitor = MatchTracker(TRACK_QUEUE, PROCESS_QUEUE, self.update_track_status, self.track_log, cat=self.track_cat)
        self.postprocess_monitor = Postprocessor(PROCESS_QUEUE, COMPLETED, self.update_postprocess_status, self.postprocess_log, cat=self.process_cat)

        self.update_tick()

    # functions to update the colorful blocks at the top
    def update_download_status(self, text, color):
        self.download_status.config(text=text, bg=color)
    def update_track_status(self, text, color):
        self.track_status.config(text=text, bg=color)
    def update_postprocess_status(self, text, color):
        self.postprocess_status.config(text=text, bg=color)

    # functions to start and pause the daemons
    def toggle_download_daemon(self):
        self.download_monitor.toggle_monitoring()
    def start_track_daemon(self):
        self.track_monitor.toggle_monitoring()
    def start_visualprocessor(self): 
        self.postprocess_monitor.visual = True
        self.postprocess_monitor.toggle_monitoring()
    def start_fastprocessor(self):
        self.postprocess_monitor.visual = False
        self.postprocess_monitor.toggle_monitoring()

    # opens a video in a way thats like typing [open video.mp4] into your terminal
    def open_selected_video(self):
        selection = self.listboxes[3].curselection() #get what element you clicked on in column 4
        if selection:
            match_name = self.listboxes[3].get([selection[0]]) 
            video_path = f"{scriptdir}/matches/{match_name}/{match_name}_final.mp4"
            print(video_path)
            if os.path.exists(video_path):
                # this is a mac command. ill work on having the equivalent on windows as well.
                subprocess.run(["open", "-a", "QuickTime Player", video_path])
            else:
                print(f"No video found in '{video_path}'")

    # clears matches in /downloadqueue
    def clear_queue(self):
        for item in os.listdir(DOWNLOAD_QUEUE):
            item_path = os.path.join(DOWNLOAD_QUEUE, item)
            os.remove(item_path)
        self.update_listboxes()
        print('cleared the queue')

    # updates the columns to be what matches are in the actual folders
    def update_listboxes(self):
        print('refrehsed')
        for i, folder in enumerate(self.columns): # enumerate lmao
            self.listboxes[i].delete(0, tk.END)
            for file in os.listdir(folder):
                self.listboxes[i].insert(tk.END, file)

    #pop up a window to let you add matches to the download queue
    def open_match_selection(self):
        popup = Toplevel(self.root)
        popup.title("Add matches to queue")
        popup.geometry("300x600")
        
        tk.Label(popup, text="enter TBA event or team key").pack(pady=10)
        
        self.entry = tk.Entry(popup, width=30) # input box
        self.entry.pack(pady=10)

        option_box = tk.Frame(popup, pady=5) #to put the buttons side by side
        option_box.pack()
        tk.Button(option_box, text="Event matches", command=self.get_event_matches).grid(row=0, column=0, padx=5)
        tk.Button(option_box, text="Team matches", command=self.get_team_matches).grid(row=0, column=1, padx=5)

        self.listed_matches = Listbox(popup, height=24, width=30, selectmode=tk.EXTENDED)
        self.listed_matches.pack(pady=10)

        def add_selected_matches():
            selected_indices = self.listed_matches.curselection()
            for index in selected_indices:
                match_name = self.listed_matches.get(index)
                file_path = os.path.join(DOWNLOAD_QUEUE, f"{match_name}")
                with open(file_path, "w") as f:
                    f.write("")  # Create an empty file
            self.update_listboxes()
            popup.destroy()

        add_button = Button(popup, text="Add Selected Matches", command=add_selected_matches)
        add_button.pack(pady=10)

    def get_event_matches(self):
        if self.listed_matches and self.entry:
            user_input = self.entry.get()
            with open (f'{scriptdir}/data/super-secret-API-key.txt', 'r') as file:
                token = file.read() # dont rate limit me pls
            url = f'https://www.thebluealliance.com/api/v3/event/{user_input}/matches/keys'
            headers = {"X-TBA-Auth-Key": token}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                print('success')
                for item in data:
                    self.listed_matches.insert(tk.END, item)
            else:
                print(f"Error: {response.status_code} - {response.text}")

                
    
    #TODO: put the two lines below in a thread (so it can't crash the entire gui)
    # def bad_append_to_logbox(self, message):  #this is supposed to be defined by class, i should have made a fourth class
    #         # self.system_status.delete(1.0, tk.END)
    #         self.system_status.insert(tk.END, message+"\n")
    #         self.system_status.yview(tk.END)
    def upload_results(self): # uploads selected matches to google sheets
        selection = self.listboxes[3].curselection()
        if selection:
            for match in selection:
                match_name = self.listboxes[3].get([match]) 
                print(match_name)
                upload_to_sheets(scriptdir, match_name) #TODO: test it

    def get_team_matches(self):
        if self.listed_matches and self.entry:
            user_input = self.entry.get()
            with open (f'{scriptdir}/data/super-secret-API-key.txt', 'r') as file:
                token = file.read() # dont rate limit me pls
            url = f'https://www.thebluealliance.com/api/v3/team/{user_input}/matches/2025/keys'
            headers = {"X-TBA-Auth-Key": token}
            response = requests.get(url, headers=headers)
            if response.status_code == 200: # if the status do be looking OK
                matches = response.json()
                for item in matches:
                    self.listed_matches.insert(tk.END, item)
            else:
                print(f"Error: {response.status_code} - {response.text}")

    def update_tick(self):
        self.download_cat.breathe() # OwO
        self.track_cat.breathe() # OwO
        self.process_cat.breathe() # OwO
        self.root.after(1000, self.update_tick) #calls another update_tick after 1 second
        

    def ben_mode(self): # CHANNELS THE FULL POWER OF BEN
        with open ('ben_mode.py') as file:  # its a shame it was .gitignored
            code = file.read() # MIIINE
            exec(code) # THE POWERRRR
    

if __name__ == "__main__":
    root = tk.Tk()
    app = MainPanel(root)
    root.mainloop()