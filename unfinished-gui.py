import os
import time
import shutil
import threading
import tkinter as tk
from tkinter import Toplevel, Listbox, Button
import requests
from capture_video import get_TBA, download_yt
import sys

scriptdir = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_QUEUE = f"{scriptdir}/processor/downloadqueue"
TRACK_QUEUE = f"{scriptdir}/processor/trackqueue"
PROCESS_QUEUE = f"{scriptdir}/processor/processqueue"

# Ensure directories exist
for folder in [DOWNLOAD_QUEUE, TRACK_QUEUE, PROCESS_QUEUE]:
    os.makedirs(folder, exist_ok=True)

class FileDownloader(threading.Thread):
    def __init__(self, source, destination, delay, update_callback):
        super().__init__(daemon=True)
        self.source = source
        self.destination = destination
        self.update_callback = update_callback
        self.files_to_process = []
        self.running = False

    def start_monitoring(self):
        if not self.running:
            self.running = True
            self.start()

    def run(self):
        while self.running:
            self.files_to_process = []
            for file in os.listdir(self.source):
                self.files_to_process.append(file)
            
            if self.files_to_process:
                file = self.files_to_process.pop(0)
                file_path = os.path.join(self.source, file)
                get_TBA(scriptdir, file)
                # download_yt(scriptdir, file)
                new_path = os.path.join(self.destination, os.path.basename(file_path))
                shutil.move(file_path, new_path)
                self.update_callback()
            
            time.sleep(1)

class ThreeColumnGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoSCout!!!")
        self.listed_matches = None
        self.entry = None

        self.columns = [DOWNLOAD_QUEUE, TRACK_QUEUE, PROCESS_QUEUE]
        self.listboxes = []

        for i, label in enumerate(["Download Queue", "Track Queue", "Process Queue"]):
            frame = tk.Frame(root)
            frame.grid(row=1, column=i, padx=10, pady=10)
            tk.Label(frame, text=label).pack()
            listbox = tk.Listbox(frame, height=15, width=30, selectmode=tk.EXTENDED)
            listbox.pack()
            self.listboxes.append(listbox)

        # Create a Text widget for displaying print statements
        self.log_box = tk.Text(root, height=10, width=50)
        self.log_box.grid(row=2, column=1, pady=10)
        sys.stdout = self  # Redirect print statements to the log box

        # Buttons to start daemons
        start_download_button = tk.Button(root, text="Start Download Daemon", command=self.start_download_daemon)
        start_download_button.grid(row=0, column=0, pady=5)

        start_track_button = tk.Button(root, text="Start Track Daemon", command=self.start_track_daemon)
        start_track_button.grid(row=0, column=1, pady=5)

        # Button to open the match selection popup
        add_button = tk.Button(root, text="Add Matches", command=self.open_match_selection)
        add_button.grid(row=2, column=0, pady=10)

        clear_button = tk.Button(root, text="Clear Queue", command=self.clear_queue)
        clear_button.grid(row=3, column=0, pady=10)

        self.update_listboxes()

        # Initialize monitoring threads
        self.download_monitor = FileDownloader(DOWNLOAD_QUEUE, TRACK_QUEUE, 3, self.update_listboxes)
        # self.track_monitor = FileMonitor(TRACK_QUEUE, PROCESS_QUEUE, 3, self.update_listboxes)

    def write(self, message):
        """Redirect print statements to the log box."""
        self.log_box.insert(tk.END, message)
        self.log_box.yview(tk.END)  # Scroll to the bottom

    def start_download_daemon(self):
        self.download_monitor.start_monitoring()

    def start_track_daemon(self):
        self.track_monitor.start_monitoring()

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
