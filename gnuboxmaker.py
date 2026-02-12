#!/usr/bin/env python3
import tkinter as tk
from PIL import Image, ImageTk

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

# ---------------------------------------- editor frame



# ---------------------------------------- open project frame

def open_project():
    print("Open Project clicked")

def new_project():
    print("New Project clicked")

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
