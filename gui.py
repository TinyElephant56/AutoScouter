import os
import time
import shutil
import threading
import tkinter as tk
from tkinter import Toplevel, Listbox, Button
import requests
from capture_video import get_TBA, download_yt
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import queue


scriptdir = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_QUEUE = f"{scriptdir}/processor/downloadqueue"
TRACK_QUEUE = f"{scriptdir}/processor/trackqueue"
PROCESS_QUEUE = f"{scriptdir}/processor/processqueue"

# Ensure directories exist
for folder in [DOWNLOAD_QUEUE, TRACK_QUEUE, PROCESS_QUEUE]:
    os.makedirs(folder, exist_ok=True)

class FileHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor

    def on_created(self, event):
        if not event.is_directory:
            app.update_listboxes()
            self.processor.add_to_queue(event.src_path)
 
class FileProcessor(threading.Thread):
    def __init__(self, source, destination, status_callback, log_box):
        super().__init__(daemon=True)
        self.source = source
        self.destination = destination
        self.running = False
        self.observer = Observer()
        self.queue = queue.Queue()
        self.status_callback = status_callback
        self.log_box = log_box

    def toggle_monitoring(self):
        if not self.running:
            self.running = True
            for file in os.listdir(self.source):
                file_path = os.path.join(self.source, file)
                if os.path.isfile(file_path):
                    self.queue.put(file_path)

            event_handler = FileHandler(self)
            self.observer.schedule(event_handler, self.source, recursive=False)
            self.observer.start()
            self.start()
            self.status_callback('started', 'green')

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

    def process_file(self, file_path):
        pass

class MatchDownloader(FileProcessor):
    def process_file(self, file_path):
        file_name = os.path.basename(file_path)

        self.status_callback(f'{file_name}: getting TBA', 'orange')
        get_TBA(scriptdir, file_name)

        self.status_callback(f'{file_name}: getting video', 'orange')
        download_yt(scriptdir, file_name)

        self.status_callback(f'{file_name}: success', 'green')
        new_path = os.path.join(self.destination, file_name)
        shutil.move(file_path, new_path)

        app.update_listboxes()

class MatchTracker(FileProcessor):
    def process_file(self, file_path):
        print('processing!')
        file_name = os.path.basename(file_path)
        self.status_callback(f'{file_name}: tracking', 'orange')

        time.sleep(5)
        
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

        sys.stdout = self 
    
        self.columns = [DOWNLOAD_QUEUE, TRACK_QUEUE, PROCESS_QUEUE]
        self.listboxes = []

        for i in range(3):
            frame = tk.Frame(root)
            frame.grid(row=2, column=i, padx=10, pady=10)
            listbox = tk.Listbox(frame, height=15, width=30, selectmode=tk.EXTENDED)
            listbox.pack()
            self.listboxes.append(listbox)

        self.download_status = tk.Label(root, text="Downloader not running", bg="gray", fg="white", width=30, height=2)
        self.download_status.grid(row=1, column=0, pady=10)
        self.track_status = tk.Label(root, text="Tracker not running", bg="gray", fg="white", width=30, height=2)
        self.track_status.grid(row=1, column=1, pady=10)

        self.download_log = tk.Text(root, height=10, width=30)
        self.download_log.grid(row=5, column=0, pady=10)
        self.track_log = tk.Text(root, height=10, width=30)
        self.track_log.grid(row=5, column=1, pady=10)

        start_track_button = tk.Button(root, text="Start Track Daemon", command=self.start_track_daemon)
        start_track_button.grid(row=0, column=1, pady=5)

        button_box = tk.Frame(root, pady=5)
        button_box.grid(row=4, column=0)
        tk.Button(button_box, text="Add Matches", command=self.open_match_selection).grid(row=1, column=0, pady=5)
        tk.Button(button_box, text="Clear Queue", command=self.clear_queue).grid(row=1, column=1, pady=5)
        tk.Button(button_box, text="Activate Downloader", command=self.toggle_download_daemon).grid(row=0, column=0, pady=5)
        tk.Button(button_box, text="Refresh", command=self.update_listboxes).grid(row=0, column=1)
        
        self.update_listboxes()
        self.download_monitor = MatchDownloader(DOWNLOAD_QUEUE, TRACK_QUEUE, self.update_download_status, self.download_log)
        self.track_monitor = MatchTracker(TRACK_QUEUE, PROCESS_QUEUE, self.update_track_status, self.track_log)
    
    def update_download_status(self, text, color):
        self.download_status.config(text=text, bg=color)
    def update_track_status(self, text, color):
        self.track_status.config(text=text, bg=color)

    def toggle_download_daemon(self):
        self.download_monitor.toggle_monitoring()
    def start_track_daemon(self):
        self.track_monitor.toggle_monitoring()

    def write(self, message):
        """Redirect print statements to the log box."""
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
