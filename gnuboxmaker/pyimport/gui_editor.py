import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
from tkinter import ttk

def create_frame(gui_container, build_project):
    frame_editor = tk.Frame(gui_container)

    bottom_frame = tk.Frame(frame_editor)
    bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10)

    progress_label = tk.Label(bottom_frame, text="Nothing")
    progress_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,5))

    progress = ttk.Progressbar(bottom_frame, orient="horizontal", mode="determinate")
    progress.grid(row=1, column=0, sticky="ew")
    progress["maximum"] = 100

    build_btn = tk.Button(bottom_frame, text="Build", command=build_project)
    build_btn.grid(row=1, column=1, padx=10)

    bottom_frame.grid_columnconfigure(0, weight=1)

    def updateProgress(value=0, text=None):
        if text is None:
            text = "Nothing"

        buildLog(f"{value} : {text}")
        
        progress["value"] = value
        progress_label["text"] = text
        gui_window.update_idletasks()

    frame_editor.place(relwidth=1, relheight=1)
    return frame_editor
