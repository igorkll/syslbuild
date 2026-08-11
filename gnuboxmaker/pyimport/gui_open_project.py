import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
import __main__

def create_frame(gui_container):
    frame_openproject = tk.Frame(gui_container)

    def open_project():
        file_path = filedialog.askopenfilename(
            title="Open project (*.gnb)",
            filetypes=[("GNB files", "*.gnb")]
        )
        if file_path:
            __main__.run_editor(file_path)

    def new_project():
        folder_path = filedialog.askdirectory(title="Select empty directory for new project")
        if folder_path:
            if os.listdir(folder_path):
                messagebox.showwarning("Warning", "Directory is not empty!")
            else:
                __main__.run_editor(os.path.join(folder_path, "gnubox.gnb"))
        

    img_openproject = ImageTk.PhotoImage(Image.open("gnuboxmaker/images/openproject.png").resize((400, 400)))
    img_newproject = ImageTk.PhotoImage(Image.open("gnuboxmaker/images/newproject.png").resize((400, 400)))

    frame_openproject.grid_rowconfigure(0, weight=1)
    frame_openproject.grid_rowconfigure(1, weight=0)
    frame_openproject.grid_columnconfigure(0, weight=1)
    frame_openproject.grid_columnconfigure(1, weight=1)

    label1 = tk.Label(frame_openproject, image=img_openproject)
    label1.image = img_openproject
    label1.grid(row=0, column=0, padx=10, pady=10)

    label2 = tk.Label(frame_openproject, image=img_newproject)
    label2.image = img_newproject
    label2.grid(row=0, column=1, padx=10, pady=10)

    button1 = tk.Button(frame_openproject, text="Open Project", command=open_project)
    button1.grid(row=1, column=0, padx=10, pady=10)
    button2 = tk.Button(frame_openproject, text="New Project", command=new_project)
    button2.grid(row=1, column=1, padx=10, pady=10)

    frame_openproject.place(relwidth=1, relheight=1)
    return frame_openproject
