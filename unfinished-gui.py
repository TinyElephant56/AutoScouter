import tkinter as tk
import subprocess
import os

# Path to the matches folder
MATCHES_FOLDER = "matches"

class MatchItem:
    """ Represents a match folder containing a video file. """
    def __init__(self, folder_name):
        self.folder_name = folder_name
        self.video_path = self.find_video_file()

    def find_video_file(self):
        """ Locate the .mp4 file inside the match folder. """
        folder_path = os.path.join(MATCHES_FOLDER, self.folder_name)
        for file in os.listdir(folder_path):
            if file.endswith(".mp4"):
                return os.path.join(folder_path, file)
        return None  # No video found

    def __str__(self):
        return self.folder_name  # Display only folder name in UI


class ThreeColumnGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Match Video Organizer")

        # Data for each column (list of MatchItem objects)
        self.columns = [self.load_matches(), [], []]

        # UI Elements
        self.listboxes = []
        self.buttons = []

        for i in range(3):
            frame = tk.Frame(root)
            frame.grid(row=0, column=i, padx=10, pady=10)

            listbox = tk.Listbox(frame, height=10, selectmode=tk.SINGLE)
            listbox.pack()
            self.listboxes.append(listbox)

            button_text = "Move" if i < 2 else "Open Video"
            button = tk.Button(frame, text=button_text, command=lambda i=i: self.handle_button(i))
            button.pack()
            self.buttons.append(button)

        self.update_listboxes()

    def load_matches(self):
        """ Load all match folders from the matches directory. """
        if not os.path.exists(MATCHES_FOLDER):
            return []  # No matches folder exists
        
        return [MatchItem(folder) for folder in os.listdir(MATCHES_FOLDER) if os.path.isdir(os.path.join(MATCHES_FOLDER, folder))]

    def handle_button(self, column_index):
        if column_index < 2:
            self.move_selected(column_index)
        else:
            self.open_selected_video()

    def move_selected(self, column_index):
        listbox = self.listboxes[column_index]
        selection = listbox.curselection()

        if selection:
            index = selection[0]
            item = self.columns[column_index].pop(index)
            self.columns[column_index + 1].append(item)
            self.update_listboxes()

    def open_selected_video(self):
        listbox = self.listboxes[2]
        selection = listbox.curselection()

        if selection:
            match_item = self.columns[2][selection[0]]  # Get selected MatchItem
            print(match_item.video_path)
            if match_item.video_path and os.path.exists(match_item.video_path):
                subprocess.run(["open", "-a", "QuickTime Player", match_item.video_path])
            else:
                print(f"No video found in '{match_item.folder_name}'")

    def update_listboxes(self):
        """ Refresh the UI to show the updated lists. """
        for i, listbox in enumerate(self.listboxes):
            listbox.delete(0, tk.END)
            for item in self.columns[i]:
                listbox.insert(tk.END, str(item))  # Display folder name

if __name__ == "__main__":
    root = tk.Tk()
    app = ThreeColumnGUI(root)
    root.mainloop()
