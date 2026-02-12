#!/usr/bin/env python3
import tkinter as tk
import os
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from dataclasses import dataclass, asdict
from tkinter import ttk
import json
import subprocess
import sys

window = tk.Tk()
window.title("Gnubox maker")
window.geometry("800x600")

container = tk.Frame(window)
container.pack(fill="both", expand=True)
frame_openproject = tk.Frame(container)
frame_editor = tk.Frame(container)

for frame in (frame_openproject, frame_editor):
    frame.place(relwidth=1, relheight=1)

def show_frame(frame):
    frame.tkraise()

# ---------------------------------------- data

@dataclass
class Project:
    distro: str = "debian"
    
    debian_variant: str = "minbase"
    debian_suite: str = "bookworm"
    debian_snapshot: str = "http://snapshot.debian.org/archive/debian/20250809T133719Z"

    export_x86_64: bool = True
    export_x86_64_img_bios_mbr: bool = True
    export_x86_64_img_bios_gpt: bool = False
    export_x86_64_img_uefi_gpt: bool = True
    export_x86_64_img_bios_and_uefi_gpt: bool = False

    export_x86: bool = False
    export_x86_img_bios_mbr: bool = True
    export_x86_img_bios_gpt: bool = False

def raw_load_project(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return Project(**data)

def raw_save_project(path, proj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(proj), f, indent=2, ensure_ascii=False)

# ---------------------------------------- builder

currentProject = None
path_temp = None
path_temp_syslbuild = None
path_temp_syslbuild_file = None

def setup_architecture_build():
    pass

def generate_syslbuild_project():
    builditems = []
    architectures = []
    
    if currentProject.export_x86_64:
        architectures.append("amd64")

    if currentProject.export_x86:
        architectures.append("i386")

    syslbuild_project = {
        "architectures": architectures,
        "builditems": builditems
    }
    with open(path_temp_syslbuild_file, "w") as f:
        json.dump(syslbuild_project, f, indent=2, ensure_ascii=False)

def run_syslbuild():
    cmd = [
        "pkexec", sys.executable, os.path.abspath("syslbuild.py"),
        "--arch", "ALL", path_temp_syslbuild_file
    ]

    subprocess.run(cmd, cwd=path_temp_syslbuild)

def build_project():
    updateProgress(10, "Generating the syslbuild project...")
    generate_syslbuild_project()

    updateProgress(50, "Launching syslbuild...")
    run_syslbuild()

    updateProgress()

# ---------------------------------------- editor frame

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
    
    progress["value"] = value
    window.update_idletasks()

    progress_label["text"] = text

def run_editor(path):
    global currentProject
    global path_temp
    global path_temp_syslbuild
    global path_temp_syslbuild_file

    if os.path.isfile(path):
        currentProject = raw_load_project(path)
    else:
        currentProject = Project()
        raw_save_project(path, currentProject)

    path_temp = os.path.join(os.path.dirname(path), ".temp")
    path_temp_syslbuild = os.path.join(path_temp, "syslbuild")
    path_temp_syslbuild_file = os.path.join(path_temp_syslbuild, "project.json")
    os.makedirs(path_temp, exist_ok=True)
    os.makedirs(path_temp_syslbuild, exist_ok=True)

    show_frame(frame_editor)

# ---------------------------------------- open project frame

def open_project():
    file_path = filedialog.askopenfilename(
        title="Open project (*.gnb)",
        filetypes=[("GNB files", "*.gnb")]
    )
    if file_path:
        run_editor(file_path)

def new_project():
    folder_path = filedialog.askdirectory(title="Select empty directory for new project")
    if folder_path:
        if os.listdir(folder_path):
            messagebox.showwarning("Warning", "Directory is not empty!")
        else:
            run_editor(os.path.join(folder_path, "gnubox.gnb"))
    

img_openproject = ImageTk.PhotoImage(Image.open("images/openproject.png").resize((400, 400)))
img_newproject = ImageTk.PhotoImage(Image.open("images/newproject.png").resize((400, 400)))

frame_openproject.grid_rowconfigure(0, weight=1)
frame_openproject.grid_rowconfigure(1, weight=0)
frame_openproject.grid_columnconfigure(0, weight=1)
frame_openproject.grid_columnconfigure(1, weight=1)

label1 = tk.Label(frame_openproject, image=img_openproject)
label1.grid(row=0, column=0, padx=10, pady=10)
label2 = tk.Label(frame_openproject, image=img_newproject)
label2.grid(row=0, column=1, padx=10, pady=10)

button1 = tk.Button(frame_openproject, text="Open Project", command=open_project)
button1.grid(row=1, column=0, padx=10, pady=10)
button2 = tk.Button(frame_openproject, text="New Project", command=new_project)
button2.grid(row=1, column=1, padx=10, pady=10)

# ----------------------------------------

show_frame(frame_openproject)
window.mainloop() 
