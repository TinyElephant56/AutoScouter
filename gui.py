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
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import queue
from abc import ABC, abstractmethod


scriptdir = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_QUEUE = f"{scriptdir}/processor/downloadqueue"
TRACK_QUEUE = f"{scriptdir}/processor/trackqueue"
PROCESS_QUEUE = f"{scriptdir}/processor/processqueue"
COMPLETED = f"{scriptdir}/processor/completed"


# Ensure directories exist
for folder in [DOWNLOAD_QUEUE, TRACK_QUEUE, PROCESS_QUEUE, COMPLETED]:
    os.makedirs(folder, exist_ok=True)

class FileHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor

    def on_created(self, event):
        if not event.is_directory:
            print('yo')
            app.update_listboxes()
            self.processor.add_to_queue(event.src_path)
 
class FileProcessor(threading.Thread, ABC):
    def __init__(self, source, destination, status_callback, log_box):
        super().__init__(daemon=True)
        self.source = source
        self.destination = destination
        self.running = False
        self.observer = Observer()
        self.queue = queue.Queue()
        self.status_callback = status_callback
        self.log_box = log_box

    def add_to_queue(self, path):
        self.queue.put(path)

    def append_to_logbox(self, message):
        self.log_box.delete(1.0, tk.END)
        self.log_box.insert(tk.END, message)
        self.log_box.yview(tk.END)

    def toggle_monitoring(self):
        if not self.running:
            self.running = True
            for file in os.listdir(self.source):
                file_path = os.path.join(self.source, file)
                if os.path.isfile(file_path):
                    self.queue.put(file_path)
            if not self.observer.is_alive():
                event_handler = FileHandler(self)
                self.observer.schedule(event_handler, self.source, recursive=False)
                self.observer.start()
                self.start()

            self.status_callback('activated', 'green')
        else:
            self.running = False
            self.status_callback('pausing...', 'yellow')
    
    def run(self):
        try:
            while self.running:
                if not self.queue.empty():
                    file_path = self.queue.get()
                    self.process_file(file_path)
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    @abstractmethod
    def process_file(self, file_path):
        pass

class MatchDownloader(FileProcessor):
    def process_file(self, file_path):
        file_name = os.path.basename(file_path)

        self.status_callback(f'{file_name}: getting TBA', 'orange')
        get_TBA(scriptdir, file_name)

        self.status_callback(f'{file_name}: getting video', 'orange')
        download_yt(scriptdir, file_name, log_func=self.append_to_logbox)

        self.status_callback(f'{file_name}: success', 'green')
        new_path = os.path.join(self.destination, file_name)
        shutil.move(file_path, new_path)

        app.update_listboxes()

class MatchTracker(FileProcessor):
    def process_file(self, file_path):
        print('processing!')
        file_name = os.path.basename(file_path)
        self.status_callback(f'{file_name}: tracking', 'orange')

        get_paths(scriptdir, file_name, VISUAL=False, log_func=self.append_to_logbox)
        
        new_path = os.path.join(self.destination, file_name)
        shutil.move(file_path, new_path)
        self.status_callback(f'{file_name}: done', 'green')
        app.update_listboxes()

class Postprocessor(FileProcessor):
    def __init__(self, source, destination, status_callback, log_box):
        super().__init__(source, destination, status_callback, log_box)
        self.visual = True
    
    def process_file(self, file_path):
        print(f'e{self.visual}')
        file_name = os.path.basename(file_path)

        if self.visual:
            self.status_callback(f'{file_name}: getting paths', 'orange')
        if self.visual:
            self.status_callback(f'{file_name}: forming match video', 'orange')
        
        merge_paths(scriptdir, file_name, VIDEO=self.visual, log_func=self.append_to_logbox)

        new_path = os.path.join(self.destination, file_name)
        shutil.move(file_path, new_path)
        self.status_callback(f'{file_name}: done', 'green')
        app.update_listboxes()


class ThreeColumnGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoSCout!!!")
        self.listed_matches = None
        self.entry = None

        # sys.stdout = self 
    
        self.columns = [DOWNLOAD_QUEUE, TRACK_QUEUE, PROCESS_QUEUE, COMPLETED]
        self.listboxes = []

        for i in range(4):
            frame = tk.Frame(root)
            frame.grid(row=2, column=i, padx=10, pady=10)
            listbox = tk.Listbox(frame, height=15, width=30, selectmode=tk.EXTENDED)
            listbox.pack()
            self.listboxes.append(listbox)

        self.download_status = tk.Label(root, text="Downloader not running", bg="gray", fg="white", width=30, height=2)
        self.download_status.grid(row=1, column=0, pady=10)
        self.track_status = tk.Label(root, text="Tracker not running", bg="gray", fg="white", width=30, height=2)
        self.track_status.grid(row=1, column=1, pady=10)
        self.postprocess_status = tk.Label(root, text="Postprocessor not running", bg="gray", fg="white", width=30, height=2)
        self.postprocess_status.grid(row=1, column=2, pady=10)

        self.download_log = tk.Text(root, height=10, width=38)
        self.download_log.grid(row=5, column=0, pady=10)
        self.track_log = tk.Text(root, height=10, width=38)
        self.track_log.grid(row=5, column=1, pady=10)
        self.postprocess_log = tk.Text(root, height=10, width=38)
        self.postprocess_log.grid(row=5, column=2, pady=10)

        start_track_button = tk.Button(root, text="Start Robot Tracker", command=self.start_track_daemon)
        start_track_button.grid(row=4, column=1, pady=5)

        button_box2 = tk.Frame(root, pady=5)
        button_box2.grid(row=4, column=2)
        tk.Button(button_box2, text="Get video and cycles", command=self.start_visualprocessor).grid(row=0, column=0, pady=5)
        tk.Button(button_box2, text="Get cycles", command=self.start_fastprocessor).grid(row=1, column=0, pady=5)

        button_box0 = tk.Frame(root, pady=5)
        button_box0.grid(row=4, column=0)
        tk.Button(button_box0, text="Add Matches", command=self.open_match_selection).grid(row=1, column=0, pady=5)
        tk.Button(button_box0, text="Clear Queue", command=self.clear_queue).grid(row=1, column=1, pady=5)
        tk.Button(button_box0, text="Start", command=self.toggle_download_daemon).grid(row=0, column=0, pady=5)
        tk.Button(button_box0, text="Refresh Files", command=self.update_listboxes).grid(row=0, column=1)
        
        self.update_listboxes()
        self.download_monitor = MatchDownloader(DOWNLOAD_QUEUE, TRACK_QUEUE, self.update_download_status, self.download_log)
        self.track_monitor = MatchTracker(TRACK_QUEUE, PROCESS_QUEUE, self.update_track_status, self.track_log)
        self.postprocess_monitor = Postprocessor(PROCESS_QUEUE, COMPLETED, self.update_postprocess_status, self.postprocess_log)

    def update_download_status(self, text, color):
        self.download_status.config(text=text, bg=color)
    def update_track_status(self, text, color):
        self.track_status.config(text=text, bg=color)
    def update_postprocess_status(self, text, color):
        self.postprocess_status.config(text=text, bg=color)

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

    def write(self, message):
        self.download_log.insert(tk.END, message + '\n')
        self.download_log.yview(tk.END)

    def flush(self):
        pass

    def get_event_matches(self):
        if self.listed_matches and self.entry:
            user_input = self.entry.get()
            token = 'Fz3O8X9BRqJT8XeIs1Rcnl6rSy65NbbajU2e2V18Gc9m4vi7rG2o5QnwPUulcpz7'
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

    def clear_queue(self):
        for item in os.listdir(DOWNLOAD_QUEUE):
            item_path = os.path.join(DOWNLOAD_QUEUE, item)
            os.remove(item_path)
        self.update_listboxes()
        print('cleared the queue')

    def open_match_selection(self):
        popup = Toplevel(self.root)
        popup.title("Select Matches")
        popup.geometry("300x600")

        self.entry = tk.Entry(popup, width=30)
        self.entry.pack()

        button = tk.Button(popup, text="Submit", command=self.get_event_matches)
        button.pack()

        self.listed_matches = Listbox(popup, height=20, width=30, selectmode=tk.EXTENDED)
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

    def update_listboxes(self):
        for i, folder in enumerate(self.columns):
            self.listboxes[i].delete(0, tk.END)
            for file in os.listdir(folder):
                self.listboxes[i].insert(tk.END, file)
    

if __name__ == "__main__":
    root = tk.Tk()
    app = ThreeColumnGUI(root)
    root.mainloop()
