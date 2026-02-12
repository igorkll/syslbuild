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

# ---------------------------------------- data

HandlyeKeyVarians = ["ignore", "poweroff", "reboot", "suspend", "hibernate", "lock"]
session_user_variants = ["user", "root"]
session_mode_variants = ["wayland", "x11", "tty"]
weston_shell_variants = ["kiosk", "desktop"]

@dataclass
class Project:
    distro: str = "debian"
    
    debian_variant: str = "minbase"
    debian_suite: str = "bookworm"
    debian_snapshot: str = "http://snapshot.debian.org/archive/debian/20250809T133719Z"
    user_packages: list[str] = field(default_factory=list)

    screen_idle_time: int = 0
    HandlePowerKey: str = "poweroff"
    HandleRebootKey: str = "reboot"
    HandleSuspendKey: str = "ignore"
    HandleHibernateKey: str = "ignore"
    HandleLidSwitch: str = "ignore"

    boot_quiet: bool = True
    boot_splash: bool = True

    root_expand: bool = True
    allow_updatescript: bool = True

    weston_shell: str = "kiosk"

    session_user: str = "user"
    session_mode: str = "tty"

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

class CancelGUI(Exception):
    pass

def buildLog(logstr, quiet=False):
    if not quiet:
        logstr = f"---------------- GNUBOX MAKER: {logstr}"
    
    print(logstr)

    # log_file.write(logstr + "\n")
    # log_file.flush()

def failed_to_build():
    updateProgress(100, "Failed")
    time.sleep(2)
    updateProgress()

    messagebox.showwarning("Error", "Failed to build")

def stop_error(err):
    err = "ERROR: " + err
    buildLog(err)
    if guiLoaded:
        failed_to_build()
        raise CancelGUI()
    else:
        sys.exit(1)

def deleteAny(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

def buildExecute(cmd, checkValid=True, input_data=None, cwd=None):
    if cwd != None:
        buildLog(f"Execute command from directory ({cwd}): {cmd}")
    else:
        buildLog(f"Execute command: {cmd}")
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        cwd=cwd
    )

    if process.stdin:
        if input_data:
            buildLog(f"With input: {input_data}")
            process.stdin.write(input_data)
        process.stdin.close()

    output_lines = []
    for line in process.stdout:
        buildLog(line.rstrip(), True)
        output_lines.append(line)

    process.stdout.close()
    returncode = process.wait()

    if returncode != 0 and checkValid:
        stop_error("failed to build")

    return "\n".join(output_lines)

def writeText(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)

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

def gen_default_chroot_script():
    aaa_setup = f"""#!/bin/bash
set -e

# ------------

ln -sf /usr/share/zoneinfo/UTC /etc/localtime

cat > /etc/adjtime <<'EOF'
0.0 0 0.0
0
LOCAL
EOF

# ------------

usermod -s /runshell.sh root
useradd -m -u 10000 -s /runshell.sh user
usermod -aG video,input,audio,render user"""

    if True: # template for future setting
        aaa_setup += "\nusermod -aG sudo user"

    aaa_setup += "\n\n"

    if currentProject.session_mode == "tty":
        aaa_setup += f"""systemctl disable getty@tty2.service
systemctl mask getty@tty2.service

systemctl disable getty@tty3.service
systemctl mask getty@tty3.service

systemctl disable getty@tty4.service
systemctl mask getty@tty4.service

systemctl disable getty@tty5.service
systemctl mask getty@tty5.service

systemctl disable getty@tty6.service
systemctl mask getty@tty6.service"""
    else:
        aaa_setup += f"""systemctl disable getty.target
systemctl mask getty.target

systemctl disable getty@tty1.service
systemctl mask getty@tty1.service

systemctl disable getty@tty2.service
systemctl mask getty@tty2.service

systemctl disable getty@tty3.service
systemctl mask getty@tty3.service

systemctl disable getty@tty4.service
systemctl mask getty@tty4.service

systemctl disable getty@tty5.service
systemctl mask getty@tty5.service

systemctl disable getty@tty6.service
systemctl mask getty@tty6.service

chmod -x /sbin/agetty"""

    aaa_setup += "\n\ntouch /.chrootend"
    return aaa_setup

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
        scripts.append(f"chroot/aaa_setup.sh")
        f.write(gen_default_chroot_script())

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

        if currentProject.session_mode != "tty":
            include.append("sddm")

        if currentProject.session_mode == "weston":
            include.append("weston")
        elif currentProject.session_mode == "x11":
            include.append("xserver-xorg")
            include.append("xinit")
            include.append("x11-xserver-utils")

        include += currentProject.user_packages

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

def setup_autologin():
    etc_config = os.path.join(path_temp_syslbuild, "files", "etc_config")
    systemd_config = os.path.join(path_temp_syslbuild, "files", "systemd_config")

    if currentProject.session_mode == "tty":
        writeText(os.path.join(systemd_config, "system", "getty@tty1.service.d", "autologin.conf"), f"""[Service]
ExecStart=
ExecStart=-/sbin/agetty --skip-login --nonewline --nohints --noissue --nonewline --autologin {currentProject.session_user} --noclear %I $TERM""")
    else:
        session = "weston.desktop"
        if currentProject.session_mode == "x11":
            session = ""

        writeText(os.path.join(etc_config, "sddm.conf"), f"""[Autologin]
User={currentProject.session_user}
Session={session}
Relogin=true""")

def setup_graphic():
    etc_config = os.path.join(path_temp_syslbuild, "files", "etc_config")

    if currentProject.session_mode == "wayland":
        writeText(os.path.join(etc_config, "xdg", "weston", "weston.ini"), f"""[core]
shell={currentProject.weston_shell}-shell.so
idle-time={currentProject.screen_idle_time}

[shell]
background-color=0xff000000
allow-zap=false
panel-position=none

[keyboard]
vt-switching=false

[autolaunch]
path=/runshell.sh""")

def setup_write_files():
    etc_config = os.path.join(path_temp_syslbuild, "files", "etc_config")
    systemd_config = os.path.join(path_temp_syslbuild, "files", "systemd_config")
    user_files = os.path.join(path_temp_syslbuild, "files", "user_files")

    os.makedirs(etc_config, exist_ok=True)
    os.makedirs(systemd_config, exist_ok=True)
    os.makedirs(user_files, exist_ok=True)

    writeText(os.path.join(systemd_config, "logind.conf"), f"""[Login]
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

    writeText(os.path.join(etc_config, "locale.conf"), f"""LANG=en_US.UTF-8""")

    setup_autologin()
    setup_graphic()

    buildExecute(["cp", "-a", os.path.join(path_resources, "files") + "/.", user_files])
    shutil.copy(os.path.join(path_resources, "runshell.sh"), os.path.join(path_temp_syslbuild, "files", "runshell.sh"))

def copy_bins(name):
    output_path = os.path.join(path_temp_syslbuild, name)
    deleteAny(output_path)
    buildExecute(["cp", "-a", os.path.join("gnuboxmaker", name) + "/.", output_path])

def setup_write_bins(builditems):
    copy_bins("kernel_image")
    copy_bins("embedded-plymouth")

    builditems.append({
        "architectures": ["amd64"],

        "type": "directory",
        "name": "rootfs directory x3",
        "export": False,

        "items": [
            ["rootfs directory x2", "."],

            ["kernel_image/amd64/kernel_modules", "/usr"],
            ["kernel_image/amd64/kernel.img", "/kernel.img", [0, 0, "0755"]],

            ["embedded-plymouth/x86_64", "/", [0, 0, "0755"]]
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
            ["kernel_image/i386/kernel.img", "/kernel.img", [0, 0, "0755"]],

            ["embedded-plymouth/x86", "/", [0, 0, "0755"]]
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
    setup_write_files()

    builditems.append({
        "type": "directory",
        "name": "rootfs directory x2",
        "export": False,

        "items": [
            ["rootfs directory x1", "."],

            ["files/etc_config", "/etc", [0, 0, "0644"]],
            ["files/systemd_config", "/etc/systemd", [0, 0, "0644"]],
            ["files/runshell.sh", "/runshell.sh", [0, 0, "0755"]],

            ["custom_init.sh", "/usr/share/initramfs-tools/init", [0, 0, "0755"]],
            ["custom_init_hook.sh", "/etc/initramfs-tools/hooks/custom_init_hook.sh", [0, 0, "0755"]],

            ["files/user_files", "/", [0, 0, "0755"]],
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

            "size": "auto + (10 * 1024 * 1024)",

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

            "size": "auto + (10 * 1024 * 1024)",

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

            "size": "auto + (10 * 1024 * 1024)",

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

            "size": "auto + (10 * 1024 * 1024)",

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
    cmdline = "rw rootwait=60"

    if currentProject.root_expand:
        cmdline += " root_processing root_expand"

    if currentProject.allow_updatescript:
        cmdline += " allow_updatescript"

    if currentProject.boot_splash:
        cmdline += " minlogotime=5"

    if currentProject.boot_quiet:
        cmdline += " systemd.show_status=false rd.udev.log_level=0 clear noCursorBlink vt.global_cursor_default=0 quiet"

    if currentProject.boot_splash:
        cmdline += " splash earlysplash"

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
    cmd_base = [
        "bash", "-c",
        f"cd {path_temp_syslbuild!r} && {sys.executable!r} {os.path.abspath('syslbuild.py')!r} "
        f"--arch ALL {path_temp_syslbuild_file!r} "
        f"--temp {os.path.join(currentProjectDirectory, '.temp')!r} "
        f"--output {os.path.join(currentProjectDirectory, 'output')!r} "
        f"--lastlog {os.path.join(currentProjectDirectory, 'last.log')!r}"
    ]

    if os.geteuid() != 0:
        cmd = ["pkexec"] + cmd_base
    else:
        cmd = cmd_base

    res = subprocess.run(cmd)
    return res.returncode == 0

def updateProgress(value=0, text=None): # updateProgress stub
    if text is None:
        text = "Nothing"
    
    buildLog(f"{value} : {text}")

def build_project():
    updateProgress(10, "Generating the syslbuild project...")
    generate_syslbuild_project()

    updateProgress(50, "Launching syslbuild...")
    if run_syslbuild():
        updateProgress(100, "Completed")
        time.sleep(2)
        updateProgress()
    else:
        if guiLoaded:
            failed_to_build()
        else:
            stop_error("Failed to build")

def load_project(path):
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
    os.makedirs(os.path.join(path_resources, "files"), exist_ok=True)

    runshell_path = os.path.join(path_resources, "runshell.sh")
    if not os.path.isfile(runshell_path):
        with open(runshell_path, "w") as f:
            f.write(f"""#!/bin/bash

while true; do
    echo test
    sleep 1
done""")

    gitignore_path = os.path.join(currentProjectDirectory, ".gitignore")
    if not os.path.isfile(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("output\n")
            f.write(".temp\n")
            f.write("last.log\n")

# ---------------------------------------- console build

guiLoaded = False
if len(sys.argv) > 1:
    load_project(sys.argv[1])
    build_project()
    sys.exit(0)

# ---------------------------------------- gui base

guiLoaded = True
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
    window.update_idletasks()

def run_editor(path):
    load_project(path)
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
