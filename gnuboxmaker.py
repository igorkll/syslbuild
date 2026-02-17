#!/usr/bin/env python3
import tkinter as tk
import os
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from dataclasses import dataclass, asdict, field
from tkinter import ttk
from pathlib import Path
import shutil
import json
import subprocess
import sys
import time

# ---------------------------------------- data

HandleKey_varians = ["ignore", "poweroff", "reboot", "suspend", "hibernate", "lock"] # halt, kexec
session_user_variants = ["user", "root"]
session_mode_variants = ["wayland", "x11", "tty", "init"]
weston_shell_variants = ["kiosk", "desktop"]
splash_mode_variants = ["center", "fill", "contain", "cover"]

@dataclass
class Project:
    distro: str = "debian"
    user_packages: list[str] = field(default_factory=list)
    
    debian_variant: str = "minbase"
    debian_suite: str = "bookworm"
    debian_snapshot: str = "http://snapshot.debian.org/archive/debian/20250809T133719Z"

    screen_idle_time: int = 0
    HandlePowerKey: str = "poweroff"
    HandleRebootKey: str = "reboot"
    HandleSuspendKey: str = "ignore"
    HandleHibernateKey: str = "ignore"
    HandleLidSwitch: str = "ignore"

    boot_quiet: bool = True
    boot_splash: bool = True

    splash_bg: str = "0, 0, 0"
    splash_mode: str = "contain"
    splash_scale: float = 0.7

    root_expand: bool = True
    allow_updatescript: bool = True

    weston_shell: str = "kiosk"

    session_user: str = "user"
    session_mode: str = "tty"

    cma_m: int = 512
    minlogotime: int = 5
    cmdline: str = ""

    export_x86_64: bool = True
    export_x86: bool = False
    export_arm64: bool = False

    export_img_bios_mbr: bool = True
    export_img_bios_gpt: bool = False
    export_img_uefi_gpt: bool = True
    export_img_bios_and_uefi_gpt: bool = False

    export_img_opi_zero3: bool = False
    export_img_rpi_64: bool = False

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

def copyFile(path, fromPath):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    shutil.copy(fromPath, path)

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

    if currentProject.export_arm64:
        architectures.append("arm64")

def gen_default_chroot_script():
    if currentProject.session_mode == "wayland" or currentProject.session_mode == "x11":
        user_shell = "/usr/bin/bash"
    else:
        user_shell = "/runshell_launcher.sh"

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

truncate -s 0 /etc/issue
truncate -s 0 /etc/motd

# ------------

usermod -s {user_shell} root
useradd -m -u 10000 -s {user_shell} user
usermod -aG video,input,audio,render user"""

    aaa_setup += "\n\n"

    if currentProject.boot_splash:
        aaa_setup += f"""plymouth-set-default-theme bootlogo
cp -f /usr/share/plymouth/themes/bootlogo/bootlogo.plymouth /usr/share/plymouth/themes/default.plymouth
     
systemctl mask plymouth-start.service
systemctl mask plymouth-read-write.service
systemctl mask plymouth-switch-root-initramfs.service
systemctl mask plymouth-reboot.service
systemctl mask plymouth-poweroff.service
# systemctl mask plymouth-quit-wait.service
# systemctl mask plymouth-quit.service
systemctl mask plymouth-kexec.service
systemctl mask plymouth-switch-root.service
systemctl mask plymouth-halt.service
systemctl mask plymouth-log.service"""

    aaa_setup += "\n\n"

    if currentProject.session_mode == "tty":
        aaa_setup += f"""systemctl mask getty@tty2.service
systemctl mask getty@tty3.service
systemctl mask getty@tty4.service
systemctl mask getty@tty5.service
systemctl mask getty@tty6.service
systemctl mask serial-getty@.service
systemctl mask container-getty@.service
systemctl mask console-getty.service"""
    elif currentProject.session_mode != "init":
        aaa_setup += f"""systemctl mask getty.target
systemctl mask getty@tty1.service
systemctl mask getty@tty2.service
systemctl mask getty@tty3.service
systemctl mask getty@tty4.service
systemctl mask getty@tty5.service
systemctl mask getty@tty6.service
systemctl mask serial-getty@.service
systemctl mask container-getty@.service
systemctl mask console-getty.service

chmod -x /sbin/agetty
chmod -x /sbin/getty

systemctl enable sddm
echo "sddm shared/default-display-manager select sddm" | debconf-set-selections
systemctl set-default graphical.target"""

    aaa_setup += "\n\ntouch /.chrootend"
    return aaa_setup

def setup_chroot_script():
    chroot_project_directory = os.path.join(path_resources, "chroot")
    chroot_scripts_directory = os.path.join(path_temp_syslbuild, "chroot")
    scripts = []

    os.makedirs(chroot_scripts_directory, exist_ok=True)

    for f in sorted(Path(chroot_project_directory).iterdir(), key=lambda p: p.name):
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
            "systemd",
            "systemd-sysv",
            "systemd-resolved",
            "dbus",
            "dbus-user-session",

            "cloud-guest-utils",
            "e2fsprogs",
            "gdisk",
            "uuid-runtime",
            "sed",
            "mawk",
            "kexec-tools"
        ]

        if currentProject.export_arm64:
            include.append("firmware-linux")
            include.append("firmware-brcm80211")
            include.append("firmware-realtek")
            include.append("wireless-regdb")

        if currentProject.boot_splash:
            include.append("plymouth") # install basic plymouth files. The part will later be replaced by embedded plymouth.
            include.append("plymouth-themes")

        if currentProject.session_mode == "wayland" or currentProject.session_mode == "x11":
            include.append("sddm")
            include.append("mesa-utils")
            include.append("libgl1-mesa-dri")
            include.append("libegl1-mesa")
            include.append("libgbm1")
            include.append("libdrm2")

        if currentProject.session_mode == "wayland":
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

            "components": [
                "main",
                "contrib",
                "non-free",
                "non-free-firmware"
            ],
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
        "git_checkout": "1.5.4"
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
ExecStart=-/sbin/getty --skip-login --noissue --nohints --nonewline --autologin {currentProject.session_user} --noclear %I $TERM

[Unit]
StartLimitIntervalSec=0""")
    elif currentProject.session_mode != "init":
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
locking=false
binding-modifier=none
animation=none
close-animation=none
startup-animation=none
focus-animation=none

[keyboard]
vt-switching=false

[autolaunch]
path=/runshell_launcher.sh
watch=true""")

def setup_bootlogo():
    bootlogo_files = os.path.join(path_temp_syslbuild, "files", "bootlogo")
    project_logo_path = os.path.join(path_resources, "logo.png")

    if currentProject.boot_splash:
        copyFile(os.path.join(bootlogo_files, "bootlogo.plymouth"), "gnuboxmaker/bootlogo.plymouth")
    copyFile(os.path.join(bootlogo_files, "logo.png"), project_logo_path)

    if currentProject.splash_mode == "fill":
        scale_code = f"""scaled_width = window_width;
scaled_height = window_height;"""
    elif currentProject.splash_mode == "center":
        scale_code = f"""scaled_width = img_width;
scaled_height = img_height;"""
    elif currentProject.splash_mode == "cover":
        scale_code = f"""img_scale = Math.Max(window_width / img_width, window_height / img_height);
scaled_width = Math.Int(img_width * img_scale);
scaled_height = Math.Int(img_height * img_scale);"""
    else:
        scale_code = f"""img_scale = Math.Min(window_width / img_width, window_height / img_height);
scaled_width = Math.Int(img_width * img_scale);
scaled_height = Math.Int(img_height * img_scale);"""

    writeText(os.path.join(bootlogo_files, "bootlogo.script"), f"""Window.SetBackgroundTopColor({currentProject.splash_bg});
Window.SetBackgroundBottomColor({currentProject.splash_bg});

image = Image("logo.png");

window_width = Window.GetWidth();
window_height = Window.GetHeight();
img_width = image.GetWidth();
img_height = image.GetHeight();

{scale_code}

scaled_width = scaled_width * {currentProject.splash_scale};
scaled_height = scaled_height * {currentProject.splash_scale};

scaled_image = image.Scale(scaled_width, scaled_height);
x = (window_width - scaled_width) / 2;
y = (window_height - scaled_height) / 2;

image_sprite = Sprite(scaled_image);
image_sprite.SetX(x);
image_sprite.SetY(y);
image_sprite.SetZ(-1);""")

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

    writeText(os.path.join(systemd_config, "journald.conf"), f"""[Journal]
ForwardToSyslog=no
ForwardToKMsg=no
ForwardToConsole=no
ForwardToWall=no
MaxLevelWall=emerg""")

    writeText(os.path.join(etc_config, "pam.d", "login"), f"""@include common-auth
@include common-account
@include common-session""")

    writeText(os.path.join(etc_config, "locale.conf"), f"""LANG=en_US.UTF-8""")

    setup_autologin()
    setup_bootlogo()
    setup_graphic()

    buildExecute(["cp", "-a", os.path.join(path_resources, "files") + "/.", user_files])
    shutil.copy(os.path.join(path_resources, "runshell.sh"), os.path.join(path_temp_syslbuild, "files", "runshell.sh"))
    shutil.copy(os.path.join(path_resources, "preinit.sh"), os.path.join(path_temp_syslbuild, "files", "preinit.sh"))
    shutil.copy("gnuboxmaker/runshell_launcher.sh", os.path.join(path_temp_syslbuild, "files", "runshell_launcher.sh"))

def copy_bins(name):
    output_path = os.path.join(path_temp_syslbuild, name)
    deleteAny(output_path)
    buildExecute(["cp", "-a", os.path.join("gnuboxmaker", name) + "/.", output_path])

def setup_write_bins(builditems):
    copy_bins("kernel_image")
    copy_bins("blobs")

    # ---------------------- x86_64
    items = [
        ["rootfs directory x2", "."],
        ["kernel_image/amd64/kernel_modules", "/usr"],
        ["kernel_image/amd64/kernel.img", "/kernel.img", [0, 0, "0755"]]
    ]

    if currentProject.boot_splash:
        copy_bins("embedded-plymouth")
        items.append(["embedded-plymouth/x86_64", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["amd64"],

        "type": "directory",
        "name": "rootfs directory x3",
        "export": False,

        "items": items
    })

    # ---------------------- x86
    items = [
        ["rootfs directory x2", "."],
        ["kernel_image/i386/kernel_modules", "/usr"],
        ["kernel_image/i386/kernel.img", "/kernel.img", [0, 0, "0755"]]
    ]

    if currentProject.boot_splash:
        items.append(["embedded-plymouth/x86", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["i386"],

        "type": "directory",
        "name": "rootfs directory x3",
        "export": False,

        "items": items
    })

    # ---------------------- arm64
    items = [
        ["rootfs directory x2", "."]
    ]

    if currentProject.export_img_opi_zero3:
        items.append(["kernel_image/arm64/opi_zero3/kernel_modules", "/usr"])

    if currentProject.export_img_rpi_64:
        items.append(["kernel_image/arm64/rpi_64/kernel_modules", "/usr"])

    if currentProject.boot_splash:
        items.append(["embedded-plymouth/arm64", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["arm64"],

        "type": "directory",
        "name": "rootfs directory x3",
        "export": False,

        "items": items
    })

def setup_export_initramfs(builditems):
    if currentProject.distro == "debian":
        builditems.append({
            "architectures": ["amd64"],
            
            "type": "debian-export-initramfs",
            "name": "initramfs.img",
            "export": False,

            "kernel_config": "kernel_image/amd64/kernel_config",
            "source": "rootfs directory x4"
        })

        builditems.append({
            "architectures": ["i386"],

            "type": "debian-export-initramfs",
            "name": "initramfs.img",
            "export": False,

            "kernel_config": "kernel_image/i386/kernel_config",
            "source": "rootfs directory x4"
        })

        if currentProject.export_img_opi_zero3:
            builditems.append({
                "architectures": ["arm64"],

                "type": "debian-export-initramfs",
                "name": "initramfs_opi_zero3.img",
                "export": False,

                "kernel_config": "kernel_image/arm64/opi_zero3/kernel_config",
                "source": "rootfs directory x4"
            })

        if currentProject.export_img_rpi_64:
            builditems.append({
                "architectures": ["arm64"],

                "type": "debian-export-initramfs",
                "name": "initramfs_rpi_64.img",
                "export": False,

                "kernel_config": "kernel_image/arm64/rpi_64/kernel_config",
                "source": "rootfs directory x4"
            })
    else:
        stop_error(f"unknown distro \"{currentProject.distro}\"")

def setup_build_base(builditems):
    setup_build_distro(builditems)
    setup_write_files()

    builditem = {
        "type": "directory",
        "name": "rootfs directory x2",
        "export": False,

        "directories": [],

        "items": [
            ["rootfs directory x1", "."],

            ["files/etc_config", "/etc", [0, 0, "0755"]],
            ["files/systemd_config", "/etc/systemd", [0, 0, "0755"]],
            ["files/runshell.sh", "/runshell.sh", [0, 0, "0755"]],
            ["files/runshell_launcher.sh", "/runshell_launcher.sh", [0, 0, "0755"]],
            ["files/preinit.sh", "/preinit.sh", [0, 0, "0755"]],

            ["custom_init.sh", "/usr/share/initramfs-tools/init", [0, 0, "0755"]],
            ["custom_init_hook.sh", "/etc/initramfs-tools/hooks/custom_init_hook.sh", [0, 0, "0755"]],

            ["files/user_files", "/", [0, 0, "0755"]],
        ],

        "delete": []
    }

    if currentProject.boot_splash:
        builditem["directories"].append(["/usr/share/plymouth/themes/bootlogo", [0, 0, "0755"]])
        builditem["items"].append(["files/bootlogo", "/usr/share/plymouth/themes/bootlogo", [0, 0, "0644"]])

    builditems.append(builditem)

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
        "architectures": ["amd64", "i386"],

        "type": "directory",
        "name": "rootfs directory x5",
        "export": False,

        "items": [
            ["rootfs directory x4", "."],
            ["initramfs.img", "/initramfs.img", [0, 0, "0755"]]
        ]
    })

    builditems.append({
        "architectures": ["arm64"],

        "type": "directory",
        "name": "rootfs directory x5",
        "export": False,

        "items": [
            ["rootfs directory x4", "."]
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

def setup_build_targets(builditems, cmdline):
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

    if currentProject.export_img_opi_zero3:
        builditems.append({
            "architectures": ["arm64"],

            "type": "singleboard",
            "name": f"{currentProjectName} OPI ZERO 3.img",
            "export": True,

            "singleboardType": "uboot-16",

            "bootloader": "blobs/u-boot-sunxi-with-spl.bin",
            "bootloaderDtb": "sun50i-h618-orangepi-zero3.dtb",
            "dtbList": [
                "kernel_image/arm64/opi_zero3/sun50i-h618-orangepi-zero3.dtb"
            ],

            "kernel": "kernel_image/arm64/opi_zero3/kernel.img",
            "initramfs": "initramfs_opi_zero3.img",
            "rootfs": "rootfs.img",

            "kernel_args_auto": True,
            "kernel_rootfs_auto": "manual",
            "kernel_args": cmdline + " waitFbBeforeModules console=tty1" # why is "waitFbBeforeModules" here? because in this FUCKING Chinese board, half of the peripherals start with a fucking delay, and it should be initialized by the time plymouth is launched
        })

    if currentProject.export_img_rpi_64:
        writeText(os.path.join(path_temp_syslbuild, "files", "cmdline_rpi_64.txt"), "root=/dev/mmcblk0p2 " + cmdline + " console=tty1\n")
        writeText(os.path.join(path_temp_syslbuild, "files", "config_rpi_64.txt"), f"""# For more options and information see
# http://rptl.io/configtxt
# Some settings may impact device functionality. See link above for details

# Uncomment some or all of these to enable the optional hardware interfaces
#dtparam=i2c_arm=on
#dtparam=i2s=on
#dtparam=spi=on

# Enable audio (loads snd_bcm2835)
dtparam=audio=on

# Additional overlays and parameters are documented
# /boot/firmware/overlays/README

# Automatically load overlays for detected cameras
camera_auto_detect=1

# Automatically load overlays for detected DSI displays
display_auto_detect=1

# Automatically load initramfs files, if found
auto_initramfs=1

# Enable DRM VC4 V3D driver
dtoverlay=vc4-kms-v3d
max_framebuffers=2

# Don't have the firmware create an initial video= setting in cmdline.txt.
# Use the kernel's default instead.
disable_fw_kms_setup=1

# Run in 64-bit mode
arm_64bit=1

# Disable compensation for displays with overscan
disable_overscan=1

# Run as fast as firmware / board allows
arm_boost=1

[cm4]
# Enable host mode on the 2711 built-in XHCI USB controller.
# This line should be removed if the legacy DWC2 controller is required
# (e.g. for USB device mode) or if USB support is not required.
otg_mode=1

[cm5]
dtoverlay=dwc2,dr_mode=host

[all]
disable_splash=1
boot_delay=0
avoid_warnings=1
disable_fw_kms_setup=1
""")

        builditems.append({
            "architectures": ["arm64"],

            "type": "gitclone",
            "name": "rpi_64_firmware",
            "export": False,

            "git_url": "https://github.com/raspberrypi/firmware",
            "git_branch": "master",
            "git_checkout": "1.20250915"
        })

        builditems.append({
            "architectures": ["arm64"],

            "type": "directory",
            "name": "boot_rpi_64",
            "export": False,

            "items": [
                ["rpi_64_firmware/boot/COPYING.linux", "/COPYING.linux"],
                ["rpi_64_firmware/boot/LICENCE.broadcom", "/LICENCE.broadcom"],
                ["rpi_64_firmware/boot/overlays", "/overlays"],
                ["rpi_64_firmware/boot/fixup.dat", "/fixup.dat"],
                ["rpi_64_firmware/boot/fixup4.dat", "/fixup4.dat"],
                ["rpi_64_firmware/boot/fixup4cd.dat", "/fixup4cd.dat"],
                ["rpi_64_firmware/boot/fixup4db.dat", "/fixup4db.dat"],
                ["rpi_64_firmware/boot/fixup4x.dat", "/fixup4x.dat"],
                ["rpi_64_firmware/boot/fixup_cd.dat", "/fixup_cd.dat"],
                ["rpi_64_firmware/boot/fixup_db.dat", "/fixup_db.dat"],
                ["rpi_64_firmware/boot/fixup_x.dat", "/fixup_x.dat"],
                ["rpi_64_firmware/boot/start.elf", "/start.elf"],
                ["rpi_64_firmware/boot/start4.elf", "/start4.elf"],
                ["rpi_64_firmware/boot/start4cd.elf", "/start4cd.elf"],
                ["rpi_64_firmware/boot/start4db.elf", "/start4db.elf"],
                ["rpi_64_firmware/boot/start4x.elf", "/start4x.elf"],
                ["rpi_64_firmware/boot/start_cd.elf", "/start_cd.elf"],
                ["rpi_64_firmware/boot/start_db.elf", "/start_db.elf"],
                ["rpi_64_firmware/boot/start_x.elf", "/start_x.elf"],
                ["rpi_64_firmware/boot/bootcode.bin", "/bootcode.bin"],

                ["kernel_image/arm64/rpi_64/boot", "/"],
                ["kernel_image/arm64/rpi_64/kernel.img", "/kernel8.img"],
                ["kernel_image/arm64/rpi_64/kernel_config", "/kernel8_config"],
                ["initramfs_rpi_64.img", "/initramfs8"],

                ["files/cmdline_rpi_64.txt", "/cmdline.txt"],
                ["files/config_rpi_64.txt", "/config.txt"]
            ]
        })

        builditems.append({
            "architectures": ["arm64"],

            "type": "filesystem",
            "name": "boot_rpi_64.img",
            "export": False,

            "source": "boot_rpi_64",

            "fs_type": "fat32",
            "size": "(auto * 1.2) + (100 * 1024 * 1024)",
            "minsize": "64MB",
            "label": "BOOT"
        })

        builditems.append({
            "architectures": ["arm64"],

            "type": "full-disk-image",
            "name": f"{currentProjectName} RPI 64.img",
            "export": True,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "dos",
            "partitions": [
                ["boot_rpi_64.img", "c"],
                ["rootfs.img", "linux"]
            ]
        })

def generate_syslbuild_project():
    cmdline = f"rw rootwait=60 makevartmp cma={currentProject.cma_m}M plymouth.ignore-serial-consoles preinit=/root/preinit.sh {currentProject.cmdline}"

    if currentProject.root_expand:
        cmdline += " root_processing root_expand"

    if currentProject.allow_updatescript:
        cmdline += " allow_updatescript"

    if currentProject.boot_splash:
        cmdline += f" minlogotime={currentProject.minlogotime}"

    if currentProject.boot_quiet:
        cmdline += " systemd.show_status=false rd.systemd.show_status=false udev.log_level=0 rd.udev.log_level=0 systemd.log_level=emerg systemd.log_target=null clear noCursorBlink vt.global_cursor_default=0 quiet"

    if currentProject.boot_splash:
        cmdline += " splash earlysplash"

    if currentProject.session_mode == "init":
        cmdline += " init=/runshell.sh"

    architectures = []
    builditems = []

    deleteAny(os.path.join(path_temp_syslbuild, "files"))
    deleteAny(os.path.join(path_temp_syslbuild, "chroot"))
    deleteAny(os.path.join(path_temp_syslbuild, "kernel_image"))
    deleteAny(os.path.join(path_temp_syslbuild, "blobs"))
    deleteAny(os.path.join(path_temp_syslbuild, "embedded-plymouth"))
    
    setup_build_architectures(architectures)
    setup_download(builditems)
    setup_build_base(builditems)
    setup_build_targets(builditems, cmdline)

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
    # надо при сборке из tty вместо pkexec заюзать sudo

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
        # raw_save_project(path, currentProject)
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
        copyFile(runshell_path, "gnuboxmaker/runshell.sh")

    preinit_path = os.path.join(path_resources, "preinit.sh")
    if not os.path.isfile(preinit_path):
        copyFile(preinit_path, "gnuboxmaker/preinit.sh")

    logo_path = os.path.join(path_resources, "logo.png")
    if not os.path.isfile(logo_path):
        copyFile(logo_path, "gnuboxmaker.png")

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
    

img_openproject = ImageTk.PhotoImage(Image.open("gnuboxmaker/images/openproject.png").resize((400, 400)))
img_newproject = ImageTk.PhotoImage(Image.open("gnuboxmaker/images/newproject.png").resize((400, 400)))

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
