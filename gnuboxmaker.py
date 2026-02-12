#!/usr/bin/env python3
import tkinter as tk
import os
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from dataclasses import dataclass, asdict
from tkinter import ttk
from pathlib import Path
import shutil
import json
import subprocess
import sys
import time

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

HandlyeKeyVarians = ["ignore", "poweroff", "reboot", "suspend", "hibernate", "lock"]

@dataclass
class Project:
    distro: str = "debian"
    
    debian_variant: str = "minbase"
    debian_suite: str = "bookworm"
    debian_snapshot: str = "http://snapshot.debian.org/archive/debian/20250809T133719Z"

    screen_idle_time: int = 0
    HandlePowerKey: str = "poweroff"
    HandleRebootKey: str = "reboot"
    HandleSuspendKey: str = "suspend"
    HandleHibernateKey: str = "hibernate"
    HandleLidSwitch: str = "lock"

    export_x86_64: bool = True
    export_x86: bool = False

    export_img_bios_mbr: bool = True
    export_img_bios_gpt: bool = False
    export_img_uefi_gpt: bool = True
    export_img_bios_and_uefi_gpt: bool = False

def raw_load_project(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return Project(**data)

def raw_save_project(path, proj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(proj), f, indent=2, ensure_ascii=False)

# ---------------------------------------- functions

def stop_error(err):
    err = "ERROR: " + err
    print(err)

def deleteAny(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

# ---------------------------------------- builder

currentProject = None
currentProjectName = None
currentProjectDirectory = None

path_temp = None
path_resources = None
path_temp_syslbuild = None
path_temp_syslbuild_file = None

def setup_build_architectures(architectures):
    if currentProject.export_x86_64:
        architectures.append("amd64")

    if currentProject.export_x86:
        architectures.append("i386")

def setup_chroot_script():
    chroot_project_directory = os.path.join(path_resources, "chroot")
    chroot_scripts_directory = os.path.join(path_temp_syslbuild, "chroot")
    scripts = []

    os.makedirs(chroot_scripts_directory, exist_ok=True)

    for f in Path(chroot_project_directory).iterdir():
        if f.is_file():
            scripts.append(f"chroot/{f.name}")
            shutil.copy(
                os.path.join(chroot_project_directory, f.name),
                os.path.join(chroot_scripts_directory, f.name)
            )

    with open(os.path.join(chroot_scripts_directory, "aaa_setup.sh"), "w") as f:
        f.write("#!/bin/bash\n")

    return scripts

def setup_build_distro(builditems):
    if currentProject.distro == "debian":
        include = [
            "initramfs-tools",
            "plymouth", # install basic plymouth files. The part will later be replaced by embedded plymouth.
            "plymouth-themes",

            "systemd",
            "systemd-sysv",
            "systemd-resolved",
            "dbus",
            "dbus-user-session"
        ]

        builditems.append({
            "type": "debian",
            "name": "rootfs directory x1",
            "export": False,

            "include": include,

            "variant": currentProject.debian_variant,
            "suite": currentProject.debian_suite,
            "url": currentProject.debian_snapshot
        })
    else:
        stop_error(f"unknown distro \"{currentProject.distro}\"")

def setup_download(builditems):
    builditems.append({
        "type": "gitclone",
        "name": "custom-debian-initramfs-init",
        "export": False,

        "git_url": "https://github.com/igorkll/custom-debian-initramfs-init",
        "git_checkout": "1.5.2"
    })

    def addExtract(fromdir, name):
        builditems.append({
            "type": "from-directory",
            "name": name,
            "export": False,

            "source": fromdir,
            "path": f"/{name}"
        })

    addExtract("custom-debian-initramfs-init", "custom_init.sh")
    addExtract("custom-debian-initramfs-init", "custom_init_hook.sh")

def setup_write_configs():
    etc_config = os.path.join(path_temp_syslbuild, "files", "etc_config")
    systemd_config = os.path.join(path_temp_syslbuild, "files", "systemd_config")

    os.makedirs(etc_config, exist_ok=True)
    os.makedirs(systemd_config, exist_ok=True)

    with open(os.path.join(systemd_config, "logind.conf"), "w") as f:
        f.write(f"""[Login]
NAutoVTs=0
ReserveVT=0

IdleAction=ignore

HandlePowerKey={currentProject.HandlePowerKey}
HandlePowerKeyLongPress={currentProject.HandlePowerKey}
PowerKeyIgnoreInhibited=no

HandleRebootKey={currentProject.HandleRebootKey}
HandleRebootKeyLongPress={currentProject.HandleRebootKey}
RebootKeyIgnoreInhibited=no

HandleSuspendKey={currentProject.HandleSuspendKey}
HandleSuspendKeyLongPress={currentProject.HandleSuspendKey}
SuspendKeyIgnoreInhibited=no

HandleHibernateKey={currentProject.HandleHibernateKey}
HandleHibernateKeyLongPress={currentProject.HandleHibernateKey}
HibernateKeyIgnoreInhibited=no

HandleLidSwitch={currentProject.HandleLidSwitch}
HandleLidSwitchExternalPower={currentProject.HandleLidSwitch}
HandleLidSwitchDocked={currentProject.HandleLidSwitch}
LidSwitchIgnoreInhibited=no""")

def copy_bins(name):
    output_path = os.path.join(path_temp_syslbuild, name)
    deleteAny(output_path)
    shutil.copytree(os.path.join("gnuboxmaker", name), output_path)

def setup_write_bins(builditems):
    copy_bins("kernel_image")

    builditems.append({
        "architectures": ["amd64"],

        "type": "directory",
        "name": "rootfs directory x3",
        "export": False,

        "items": [
            ["rootfs directory x2", "."],

            ["kernel_image/amd64/kernel_modules", "/usr"],
            ["kernel_image/amd64/kernel.img", "/kernel.img", [0, 0, "0755"]]
        ]
    })

    builditems.append({
        "architectures": ["i386"],

        "type": "directory",
        "name": "rootfs directory x3",
        "export": False,

        "items": [
            ["rootfs directory x2", "."],

            ["kernel_image/i386/kernel_modules", "/usr"],
            ["kernel_image/i386/kernel.img", "/kernel.img", [0, 0, "0755"]]
        ]
    })

def setup_export_initramfs(builditems):
    if currentProject.distro == "debian":
        builditems.append({
            "architectures": ["amd64"],
            
            "type": "debian-export-initramfs",
            "name": "initramfs.img",
            "export": False,

            "kernel_config": "kernel_image/amd64/kernel_config",
            "source": "rootfs directory x3"
        })

        builditems.append({
            "architectures": ["i386"],

            "type": "debian-export-initramfs",
            "name": "initramfs.img",
            "export": False,

            "kernel_config": "kernel_image/i386/kernel_config",
            "source": "rootfs directory x3"
        })
    else:
        stop_error(f"unknown distro \"{currentProject.distro}\"")

def setup_build_base(builditems):
    setup_build_distro(builditems)
    setup_write_configs()

    builditems.append({
        "type": "directory",
        "name": "rootfs directory x2",
        "export": False,

        "items": [
            ["rootfs directory x1", "."],

            ["files/etc_config", "/etc", [0, 0, "0644"]],
            ["files/systemd_config", "/etc/systemd", [0, 0, "0644"]],

            ["custom_init.sh", "/usr/share/initramfs-tools/init", [0, 0, "0755"]],
            ["custom_init_hook.sh", "/etc/initramfs-tools/hooks/custom_init_hook.sh", [0, 0, "0755"]]
        ]
    })

    setup_write_bins(builditems)

    builditems.append({
        "type": "smart-chroot",
        "name": "rootfs directory x4",
        "export": False,

        "manual_validation": True,
        "use_systemd_container": True,
        "source": "rootfs directory x3",
        "scripts": setup_chroot_script()
    })

    setup_export_initramfs(builditems)

    builditems.append({
        "type": "directory",
        "name": "rootfs directory x5",
        "export": False,

        "items": [
            ["rootfs directory x4", "."],
            ["initramfs.img", "/initramfs.img", [0, 0, "0755"]]
        ]
    })

    builditems.append({
        "type": "filesystem",
        "name": "rootfs.img",
        "export": False,

        "source": "rootfs directory x5",

        "fs_type": "ext4",
        "size": "(auto * 1.2) + (100 * 1024 * 1024)", 
        "minsize": "64MB",
        "label": "rootfs"
    })

def setup_build_targets(builditems):
    if currentProject.export_img_bios_mbr:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{currentProjectName} BIOS MBR.img",
            "export": True,

            "size": "auto + (1 * 1024 * 1024)",

            "partitionTable": "dos",
            "partitions": [
                ["rootfs.img", "linux"]
            ],

            "bootloader": {
                "type": "grub",
                "config": "grub.cfg",
                "boot": 0,
                "modules": [
                    "normal",
                    "part_msdos",
                    "part_gpt",
                    "ext2",
                    "configfile"
                ]
            }
        })

    if currentProject.export_img_bios_gpt or currentProject.export_img_bios_and_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "filesystem",
            "name": "bios boot.img",
            "export": False,

            "size": "1M"
        })

    if currentProject.export_img_bios_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{currentProjectName} BIOS GPT.img",
            "export": True,

            "size": "auto + (1 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["bios boot.img", "bios"],
                ["rootfs.img", "linux"]
            ],

            "bootloader": {
                "type": "grub",
                "config": "grub.cfg",
                "boot": 1,
                "modules": [
                    "normal",
                    "part_msdos",
                    "part_gpt",
                    "ext2",
                    "configfile"
                ]
            }
        })

    if currentProject.export_img_uefi_gpt or currentProject.export_img_bios_and_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "filesystem",
            "name": "uefi boot.img",
            "export": False,

            "fs_arg": "-F32",
            "fs_type": "fat",
            "size": "256M",
            "label": "EFI"
        })

    if currentProject.export_img_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{currentProjectName} UEFI GPT.img",
            "export": True,

            "size": "auto + (1 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["uefi boot.img", "efi"],
                ["rootfs.img", "linux"]
            ],

            "bootloader": {
                "type": "grub",
                "config": "grub.cfg",
                "esp": 0,
                "boot": 1,
                "modules": [
                    "normal",
                    "part_msdos",
                    "part_gpt",
                    "ext2",
                    "configfile"
                ]
            }
        })

    if currentProject.export_img_bios_and_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{currentProjectName} BIOS UEFI GPT.img",
            "export": True,

            "size": "auto + (1 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["bios boot.img", "bios"],
                ["uefi boot.img", "efi"],
                ["rootfs.img", "linux"]
            ],

            "bootloader": {
                "type": "grub",
                "config": "grub.cfg",
                "esp": 1,
                "boot": 2,
                "efiAndBios": True,
                "modules": [
                    "normal",
                    "part_msdos",
                    "part_gpt",
                    "ext2",
                    "configfile"
                ]
            }
        })

def generate_syslbuild_project():
    cmdline = "rw rootwait=60 systemd.show_status=false rd.udev.log_level=0 minlogotime=5 clear noCursorBlink vt.global_cursor_default=0 root_processing root_expand allow_updatescript quiet splash earlysplash"

    architectures = []
    builditems = []

    deleteAny(os.path.join(path_temp_syslbuild, "files"))
    deleteAny(os.path.join(path_temp_syslbuild, "chroot"))
    
    setup_build_architectures(architectures)
    setup_download(builditems)
    setup_build_base(builditems)
    setup_build_targets(builditems)

    syslbuild_project = {
        "architectures": architectures,
        "builditems": builditems
    }

    with open(path_temp_syslbuild_file, "w") as f:
        json.dump(syslbuild_project, f, indent=2, ensure_ascii=False)

    with open(os.path.join(path_temp_syslbuild, "grub.cfg"), "w") as f:
        f.write(f"""set cmdline="{cmdline}"

probe --set root_fs_uuid --fs-uuid $root
linux /kernel.img root=UUID=$root_fs_uuid ${{cmdline}}
initrd /initramfs.img
boot""")

def run_syslbuild():
    cmd = [
        "pkexec", "bash", "-c",
        f"cd {path_temp_syslbuild!r} && {sys.executable!r} {os.path.abspath('syslbuild.py')!r} "
        f"--arch ALL {path_temp_syslbuild_file!r} "
        f"--temp {os.path.join(currentProjectDirectory, '.temp')!r} "
        f"--output {os.path.join(currentProjectDirectory, 'output')!r} "
        f"--lastlog {os.path.join(currentProjectDirectory, 'last.log')!r}"
    ]
    subprocess.run(cmd)

def build_project():
    updateProgress(10, "Generating the syslbuild project...")
    generate_syslbuild_project()

    updateProgress(50, "Launching syslbuild...")
    run_syslbuild()

    updateProgress(100, "Completed")
    time.sleep(2)
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
    progress_label["text"] = text
    window.update_idletasks()

def run_editor(path):
    global currentProject
    global currentProjectName
    global currentProjectDirectory
    global path_temp
    global path_resources
    global path_temp_syslbuild
    global path_temp_syslbuild_file

    if os.path.isfile(path):
        currentProject = raw_load_project(path)
    else:
        currentProject = Project()
        raw_save_project(path, currentProject)

    currentProjectDirectory = os.path.dirname(path)
    currentProjectName = os.path.basename(currentProjectDirectory)
    path_temp = os.path.join(currentProjectDirectory, ".temp")
    path_resources = os.path.join(currentProjectDirectory, "resources")
    path_temp_syslbuild = os.path.join(path_temp, "syslbuild")
    path_temp_syslbuild_file = os.path.join(path_temp_syslbuild, "project.json")

    os.makedirs(path_resources, exist_ok=True)
    os.makedirs(path_temp, exist_ok=True)
    os.makedirs(path_temp_syslbuild, exist_ok=True)

    os.makedirs(os.path.join(path_resources, "chroot"), exist_ok=True)

    gitignore_path = os.path.join(currentProjectDirectory, ".gitignore")
    if not os.path.isfile(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("output\n")
            f.write(".temp\n")
            f.write("last.log\n")

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
