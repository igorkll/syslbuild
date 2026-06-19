#!/usr/bin/env python3
import tkinter as tk
import os
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from dataclasses import dataclass, asdict, field
from tkinter import ttk
from pathlib import Path
import shutil
import json5
import json
import subprocess
import sys
import time
import syslbuild

# ---------------------------------------- data

HandleKey_varians = ["ignore", "poweroff", "reboot", "suspend", "hibernate", "lock"] # halt, kexec
session_user_variants = ["user", "root"]
session_mode_variants = ["wayland", "x11", "tty", "init"]
weston_shell_variants = ["kiosk", "desktop"]
splash_mode_variants = ["center", "fill", "contain", "cover"]
boot_sound_variants = ["none", "init", "logo"]

default_devicetree_overlays = {
#    "opi_zero3": "gnuboxmaker/kernel_build/output/arm64/opi_zero3/overlays"
}

@dataclass
class Project:
    gnubox_version: list[int] = field(default_factory=lambda: [0, 0, 0])

    distro: str = "debian"
    user_packages: list[str] = field(default_factory=list)
    exclude_packages: list[str] = field(default_factory=list)
    
    debian_variant: str = "minbase"
    debian_suite: str = "trixie"
    debian_snapshot: str = "http://snapshot.debian.org/archive/debian/20260217T143331Z"

    screen_idle_time: int = 0
    HandlePowerKey: str = "poweroff"
    HandleRebootKey: str = "reboot"
    HandleSuspendKey: str = "ignore"
    HandleHibernateKey: str = "ignore"
    HandleLidSwitch: str = "ignore"

    boot_quiet: bool = True
    boot_splash: bool = True
    boot_sound: str = "none"
    dont_show_splash_on_poweroff: bool = True
    dont_use_splash_on_efi: bool = False

    uartlogs: bool = False
    uartlogs_speed: int = 115200
    uartlogs_rootshell: bool = False
    
    exclude_tty1_from_consoles: bool = False
    exclude_tty1_from_consoles_in_quiet: bool = True
    make_tty1_primary_console: bool = False

    splash_bg: str = "0, 0, 0"
    splash_updating_bg: str = "0, 0, 0"
    splash_mode: str = "contain"
    splash_scale: float = 0.7
    use_separate_splash_for_update: bool = True

    root_expand: bool = True
    root_readonly: bool = False
    allow_updatescript: bool = False
    separate_data_partition: bool = False
    separate_data_partition_home_link: bool = True
    separate_data_partition_var_link: bool = False
    separate_data_partition_etc_link: bool = False
    var_is_temp: bool = True
    minsize_boot_partition: str = "64MB"
    minsize_efi_partition: str = "64MB"
    minsize_root_partition: str = "64MB"
    minsize_data_partition: str = "64MB"

    size_boot_partition: str = "(auto * 1.2) + (100 * 1024 * 1024)"
    size_efi_partition: str = "256MB"
    size_root_partition: str = "(auto * 1.2) + (100 * 1024 * 1024)"

    weston_shell: str = "kiosk"

    session_user: str = "user"
    session_mode: str = "tty"

    minlogotime: int = 10
    cmdline: str = ""
    exclude_cmdline: list[str] = field(default_factory=list)
    sudo_privileges: bool = False

    integrate_liamounts: bool = False
    integrate_xwayland: bool = True

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
        data = json5.load(f)
        return Project(**data)

def raw_save_project(path, proj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(proj), f, indent=2, ensure_ascii=False)

# -1 - версия проекта ниже версии тула
# 0 - версии совпадают
# 1 - версия проекта выше чем версия тула (не катит)
def checkVersion(project):
    minVersion = syslbuild.VERSION

    for index, vernum in enumerate(project.gnubox_version):
        if vernum > minVersion[index]:
            return 1
        elif vernum < minVersion[index]:
            return -1
    
    return 0

# ---------------------------------------- functions

class CancelGUI(Exception):
    pass

def exclude_string(lstr, exclude_list):
    parts = lstr.split()
    filtered = [p for p in parts if p not in exclude_list]
    return ' '.join(filtered)

def exclude_array(arr, exclude_list):
    return [item for item in arr if item not in exclude_list]

def buildLog(logstr, quiet=False):
    if not quiet:
        logstr = f"---------------- GNUBOX MAKER: {logstr}"
    
    print(logstr)

    # log_file.write(logstr + "\n")
    # log_file.flush()

def failed_to_build(err="Failed to build"):
    updateProgress(100, "Failed")
    time.sleep(2)
    updateProgress()

    messagebox.showwarning("Error", err)

def stop_error(err):
    err = "ERROR: " + err
    buildLog(err)
    if guiLoaded:
        failed_to_build(err)
        raise CancelGUI()
    else:
        sys.exit(1)

def show_error(err):
    err = "ERROR: " + err
    buildLog(err)
    if guiLoaded:
        messagebox.showwarning("Error", err)

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
        stop_error("Failed to build")

    return "\n".join(output_lines)

def writeText(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)

def copyFile(path, fromPath):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    shutil.copy(fromPath, path)

# ---------------------------------------- builder

current_project = None
current_project_name = None
current_project_directory = None

path_temp = None
path_resources = None
path_temp_syslbuild = None
path_temp_syslbuild_file = None

def setup_build_architectures(architectures):
    if current_project.export_x86_64:
        architectures.append("amd64")

    if current_project.export_x86:
        architectures.append("i386")

    if current_project.export_arm64:
        architectures.append("arm64")

def gen_default_first_chroot_script():
    if current_project.session_mode == "wayland" or current_project.session_mode == "x11":
        user_shell = "/run_session.sh"
    else:
        user_shell = "/runshell_launcher.sh"
        
    aaa_setup = f"""#!/bin/bash

# ------------

ln -sf /usr/share/zoneinfo/UTC /etc/localtime

cat > /etc/adjtime <<'EOF'
0.0 0 0.0
0
LOCAL
EOF

# ------------

systemctl mask getty.target
systemctl mask getty@.service
systemctl mask getty@tty1.service
systemctl mask getty@tty2.service
systemctl mask getty@tty3.service
systemctl mask getty@tty4.service
systemctl mask getty@tty5.service
systemctl mask getty@tty6.service
systemctl mask serial-getty@.service
systemctl mask container-getty@.service
systemctl mask console-getty.service

# ------------

if [ -d "/lib/firmware/brcm/" ]; then
    cd /lib/firmware/brcm/

    ln -sf ../cypress/cyfmac43455-sdio.bin brcmfmac43455-sdio.raspberrypi,4-model-b.bin
    ln -sf ../cypress/cyfmac43455-sdio.bin brcmfmac43455-sdio.raspberrypi,5-model-b.bin
    ln -sf ../cypress/cyfmac43430-sdio.bin brcmfmac43430-sdio.raspberrypi,3-model-b.bin
    ln -sf ../cypress/cyfmac43455-sdio.bin brcmfmac43455-sdio.raspberrypi,3-model-b-plus.bin

    cd /
fi

# ------------

systemctl set-default graphical.target

# ------------

usermod -s {user_shell} root
useradd -m -u 10000 -s {user_shell} user
usermod -aG video,input,audio,render user
mkdir -p -m 700 /home/user
chown user:user /home/user"""

    aaa_setup += "\n\n"

    if current_project.boot_splash:
        aaa_setup += f"""plymouth-set-default-theme bootlogo
cp -f /usr/share/plymouth/themes/bootlogo/bootlogo.plymouth /usr/share/plymouth/themes/default.plymouth

# this trash break systemd quiet
systemctl mask plymouth-read-write.service"""

    if current_project.dont_show_splash_on_poweroff:
        aaa_setup += "\n" + f"""systemctl mask plymouth-poweroff.service
systemctl mask plymouth-reboot.service
systemctl mask plymouth-halt.service
systemctl mask plymouth-kexec.service"""

    if current_project.integrate_liamounts:
        aaa_setup += "\n" + f"""cd /liamounts
./install.sh
cd /
rm -rf /liamounts"""

    if current_project.sudo_privileges:
        aaa_setup += "\n" + f"""echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user-nopasswd
chmod 440 /etc/sudoers.d/user-nopasswd"""

    aaa_setup += "\n\ntouch /.chrootend"
    return aaa_setup

def gen_default_last_chroot_script():
    zzz_setup = "#!/bin/bash"

    if current_project.session_mode != "init":
        zzz_setup += "\n\nsystemctl enable run_shell.service"

    if current_project.uartlogs_rootshell:
        zzz_setup += "\n\nsystemctl enable uartshell.service"

    zzz_setup += "\n\ntouch /.chrootend"

    return zzz_setup

def setup_chroot_script():
    chroot_project_directory = os.path.join(path_resources, "chroot")
    chroot_scripts_directory = os.path.join(path_temp_syslbuild, "chroot")
    scripts = []

    os.makedirs(chroot_scripts_directory, exist_ok=True)

    scripts.append(f"chroot/aaa_setup.sh")
    with open(os.path.join(chroot_scripts_directory, "aaa_setup.sh"), "w") as f:
        f.write(gen_default_first_chroot_script())

    scripts.append(f"chroot/zzz_setup.sh")
    with open(os.path.join(chroot_scripts_directory, "zzz_setup.sh"), "w") as f:
        f.write(gen_default_last_chroot_script())

    for f in sorted(Path(chroot_project_directory).iterdir(), key=lambda p: p.name):
        if f.is_file():
            scripts.append(f"chroot/{f.name}")
            shutil.copy(
                os.path.join(chroot_project_directory, f.name),
                os.path.join(chroot_scripts_directory, f.name)
            )

    return scripts

def setup_build_distro(builditems):
    if current_project.distro == "debian":
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
            "kexec-tools",
            "alsa-utils",
            "jq",

            "firmware-linux",
            "firmware-brcm80211",
            "firmware-realtek",
            "wireless-regdb"
        ]

        if current_project.sudo_privileges:
            include.append("sudo")

        # without this, no dependencies are set and nothing works. А МОЖЕТ БЛЯТЬ И НЕТ, я разберусь...
        if current_project.boot_splash or True:
            include.append("plymouth") # install basic plymouth files. The part will later be replaced by embedded plymouth.
            include.append("plymouth-themes")

        if current_project.session_mode == "wayland" or current_project.session_mode == "x11":
            include.append("mesa-utils")
            include.append("libgl1-mesa-dri")
            include.append("libgbm1")
            include.append("libdrm2")

            if current_project.debian_suite == "trixie":
                include.append("libegl1")
            else:
                include.append("libegl1-mesa")

        if current_project.session_mode == "wayland":
            include.append("weston")
            if current_project.integrate_xwayland:
                include.append("xwayland")
        elif current_project.session_mode == "x11":
            include.append("xserver-xorg")
            include.append("xinit")
            include.append("x11-xserver-utils")
            include.append("matchbox-window-manager")

        if current_project.integrate_liamounts:
            include.append("at")
            include.append("bindfs")

        include += current_project.user_packages
        include = exclude_array(include, current_project.exclude_packages)

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

            "variant": current_project.debian_variant,
            "suite": current_project.debian_suite,
            "url": current_project.debian_snapshot
        })
    else:
        stop_error(f"unknown distro \"{current_project.distro}\"")

def setup_download(builditems):
    def addDownload(name, version):
        builditems.append({
            "type": "gitclone",
            "name": name,
            "export": False,

            "git_url": f"https://github.com/igorkll/{name}",
            "git_checkout": version
        })

    def addExtract(fromdir, name):
        builditems.append({
            "type": "from-directory",
            "name": name,
            "export": False,

            "source": fromdir,
            "path": f"/{name}"
        })

    addDownload("custom-debian-initramfs-init", "1.5.10")
    addExtract("custom-debian-initramfs-init", "custom_init.sh")
    addExtract("custom-debian-initramfs-init", "custom_init_hook.sh")

    if current_project.integrate_liamounts:
        addDownload("liamounts", "2.1")

def setup_autologin():
    systemd_config = os.path.join(path_temp_syslbuild, "files", "systemd_config")

    if current_project.session_mode != "init":
        content = f"""[Unit]
Description=shell
After=graphical.target
StartLimitIntervalSec=0

[Service]
Type=simple
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=no
StandardInput=tty
StandardOutput=tty
ExecStartPre=/bin/sh -c 'stty -echo < /dev/tty1'
ExecStart=-/bin/login -f {current_project.session_user}
Restart=always
RestartSec=0

[Install]
WantedBy=graphical.target"""
        writeText(os.path.join(systemd_config, "system", "run_shell.service"), content)

    if current_project.uartlogs_rootshell:
        content = f"""[Unit]
Description=rootshell on UART
After=multi-user.target

[Service]
Type=idle
ExecStart=-/sbin/agetty --autologin root --noclear ttyS0 {current_project.uartlogs_speed} vt102
Restart=always
RestartSec=0
StandardInput=tty
StandardOutput=tty
TTYPath=/dev/ttyS0
TTYReset=yes
TTYVHangup=yes

[Install]
WantedBy=multi-user.target"""
        writeText(os.path.join(systemd_config, "system", "uartshell.service"), content)

def setup_graphic():
    etc_config = os.path.join(path_temp_syslbuild, "files", "etc_config")

    if current_project.session_mode == "wayland":
        writeText(os.path.join(etc_config, "xdg", "weston", "weston.ini"), f"""[core]
shell={current_project.weston_shell}-shell.so
idle-time={current_project.screen_idle_time}
xwayland={"true" if current_project.integrate_xwayland else "false"}

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

[libinput]
enable-tap=true

[autolaunch]
path=/runshell_launcher.sh
watch=true""")
    
    elif current_project.session_mode == "x11":
        xinitrc = "#!/bin/bash"

        if current_project.screen_idle_time > 0:
            xinitrc += "\n" + f"""xset s blank
xset s {current_project.screen_idle_time}
xset s on
xset dpms {current_project.screen_idle_time} {current_project.screen_idle_time} {current_project.screen_idle_time}
xset +dpms"""
        else:
            xinitrc += "\n" + f"""xset s off
xset -dpms"""

        xinitrc += "\nmatchbox-window-manager -use_titlebar no &"
        xinitrc += "\n/runshell_launcher.sh"

        writeText(os.path.join(etc_config, "X11", "xinit", "xinitrc"), xinitrc)

        writeText(os.path.join(etc_config, "X11", "xorg.conf.d", "10-settings.conf"), f"""Section "ServerFlags"
    Option "DontVTSwitch" "true"
    Option "DontZap" "true"
    Option "DontZoom" "true"
    Option "AllowmouseOpenfail" "true"
EndSection""")

def setup_bootlogo():
    bootlogo_files = os.path.join(path_temp_syslbuild, "files", "bootlogo")
    project_logo_path = os.path.join(path_resources, "logo.png")
    project_logo_updating_path = os.path.join(path_resources, "logo_updating.png")

    if current_project.boot_splash:
        copyFile(os.path.join(bootlogo_files, "bootlogo.plymouth"), "gnuboxmaker/bootlogo.plymouth")
        copyFile(os.path.join(bootlogo_files, "logo.png"), project_logo_path)
        copyFile(os.path.join(bootlogo_files, "logo_updating.png"), project_logo_updating_path)

    if current_project.splash_mode == "fill":
        scale_code = f"""scaled_width = window_width;
scaled_height = window_height;"""
    elif current_project.splash_mode == "center":
        scale_code = f"""scaled_width = img_width;
scaled_height = img_height;"""
    elif current_project.splash_mode == "cover":
        scale_code = f"""img_scale = Math.Max(window_width / img_width, window_height / img_height);
scaled_width = Math.Int(img_width * img_scale);
scaled_height = Math.Int(img_height * img_scale);"""
    else:
        scale_code = f"""img_scale = Math.Min(window_width / img_width, window_height / img_height);
scaled_width = Math.Int(img_width * img_scale);
scaled_height = Math.Int(img_height * img_scale);"""

    bootlogo_script = f"""
mode = Plymouth.GetMode();
if (mode == "system-upgrade") {{
    Window.SetBackgroundTopColor({current_project.splash_updating_bg});
    Window.SetBackgroundBottomColor({current_project.splash_updating_bg});

    image = Image("logo_updating.png");
}} else {{
    Window.SetBackgroundTopColor({current_project.splash_bg});
    Window.SetBackgroundBottomColor({current_project.splash_bg});

    image = Image("logo.png");
}}

window_width = Window.GetWidth();
window_height = Window.GetHeight();
img_width = image.GetWidth();
img_height = image.GetHeight();

{scale_code}

scaled_width = scaled_width * {current_project.splash_scale};
scaled_height = scaled_height * {current_project.splash_scale};

scaled_image = image.Scale(scaled_width, scaled_height);
x = (window_width - scaled_width) / 2;
y = (window_height - scaled_height) / 2;

image_sprite = Sprite(scaled_image);
image_sprite.SetX(x);
image_sprite.SetY(y);
image_sprite.SetZ(-1);"""

    writeText(os.path.join(bootlogo_files, "bootlogo.script"), bootlogo_script)

def setup_bootsound():
    project_startup_sound_wav_path = os.path.join(path_resources, "startup.wav")

    if current_project.boot_sound == "init" or (current_project.boot_sound == "logo" and current_project.boot_splash):
        copyFile(os.path.join(path_temp_syslbuild, "files", "startup.wav"), project_startup_sound_wav_path)

def compile_dts(source_path, output_path):
    """Компилирует .dts/.dtso файл в .dtb/.dtbo с символами (-@)."""
    cmd = ['dtc', '-@', '-I', 'dts', '-O', 'dtb', '-o', output_path, source_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        if os.path.isfile(output_path):
            buildLog(f"[OK] {source_path} -> {output_path}")
        else:
            stop_error(f"[FAIL] {source_path}")
    except subprocess.CalledProcessError as e:
        stop_error(f"[FAIL] {source_path}:\n  {e.stderr}", file=sys.stderr)

def prepair_devicetree(devicetree):
    for plat_name in os.listdir(devicetree):
        plat_path = os.path.join(devicetree, plat_name)
        if not os.path.isdir(plat_path):
            continue

        for file in os.listdir(plat_path):
            full_path = os.path.join(plat_path, file)
            if not os.path.isfile(full_path):
                continue

            if file.endswith('.dts'):
                out_ext = '.dtb'
            elif file.endswith('.dtso'):
                out_ext = '.dtbo'
            else:
                continue

            base_name = os.path.splitext(file)[0]
            out_file = base_name + out_ext
            out_full = os.path.join(plat_path, out_file)
            compile_dts(full_path, out_full)

def get_devicetree_override(platform):
    dt_dir = os.path.join(path_temp_syslbuild, "files", "devicetree", platform)
    if os.path.isdir(dt_dir):
        override_path = os.path.join(dt_dir, 'override.txt')
        if os.path.isfile(override_path):
            with open(override_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if len(content) > 0:
                    return content
    
    return None

def get_devicetree_overlays(platform):
    dt_dir = os.path.join(path_temp_syslbuild, "files", "devicetree", platform)
    if os.path.isdir(dt_dir):
        overlays_path = os.path.join(dt_dir, 'overlays.txt')
        if os.path.isfile(overlays_path):
            with open(overlays_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if len(content) > 0:
                    return content.splitlines()
    
    return []

def devicetree_get_files(platform, extension):
    files = []

    dt_dir = os.path.join(path_temp_syslbuild, "files", "devicetree", platform)
    if os.path.isdir(dt_dir):
        for file in sorted(os.listdir(dt_dir)):
            full_path = os.path.join(dt_dir, file)
            if not os.path.isfile(full_path):
                continue
            
            if full_path.endswith('.' + extension):
                files.append(os.path.join("files", "devicetree", platform, file))
    
    return files

def copy_files(from_path, to_path):
    buildExecute(["cp", "-a", from_path + "/.", to_path])

def setup_write_files():
    etc_config = os.path.join(path_temp_syslbuild, "files", "etc_config")
    systemd_config = os.path.join(path_temp_syslbuild, "files", "systemd_config")
    user_files = os.path.join(path_temp_syslbuild, "files", "user_files")
    devicetree = os.path.join(path_temp_syslbuild, "files", "devicetree")

    os.makedirs(etc_config, exist_ok=True)
    os.makedirs(systemd_config, exist_ok=True)
    os.makedirs(user_files, exist_ok=True)
    os.makedirs(devicetree, exist_ok=True)

    writeText(os.path.join(systemd_config, "logind.conf"), f"""[Login]
NAutoVTs=0
ReserveVT=0

IdleAction=ignore

HandlePowerKey={current_project.HandlePowerKey}
HandlePowerKeyLongPress={current_project.HandlePowerKey}
PowerKeyIgnoreInhibited=no

HandleRebootKey={current_project.HandleRebootKey}
HandleRebootKeyLongPress={current_project.HandleRebootKey}
RebootKeyIgnoreInhibited=no

HandleSuspendKey={current_project.HandleSuspendKey}
HandleSuspendKeyLongPress={current_project.HandleSuspendKey}
SuspendKeyIgnoreInhibited=no

HandleHibernateKey={current_project.HandleHibernateKey}
HandleHibernateKeyLongPress={current_project.HandleHibernateKey}
HibernateKeyIgnoreInhibited=no

HandleLidSwitch={current_project.HandleLidSwitch}
HandleLidSwitchExternalPower={current_project.HandleLidSwitch}
HandleLidSwitchDocked={current_project.HandleLidSwitch}
LidSwitchIgnoreInhibited=no""")

    writeText(os.path.join(systemd_config, "journald.conf"), f"""[Journal]
Storage=none
ForwardToSyslog=no
ForwardToKMsg=no
ForwardToConsole=no
ForwardToWall=no
MaxLevelStore=emerg
MaxLevelSyslog=emerg
MaxLevelKMsg=emerg
MaxLevelConsole=emerg
MaxLevelWall=emerg""")

    user_system_config_append = ""
    if current_project.boot_quiet:
        user_system_config_append = """LogTarget=journal
LogLevel=emerg"""

    writeText(os.path.join(systemd_config, "system.conf"), f"""[Manager]
ShowStatus={"no" if current_project.boot_quiet else "yes"}
{user_system_config_append}""")

    writeText(os.path.join(systemd_config, "user.conf"), f"""[Manager]
{user_system_config_append}""")

    writeText(os.path.join(systemd_config, "coredump.conf"), f"""[Coredump]
Storage=none""")

    writeText(os.path.join(etc_config, "pam.d", "login"), f"""@include common-auth
@include common-account
@include common-session""")

    writeText(os.path.join(etc_config, "locale.conf"), f"""LANG=en_US.UTF-8""")

    setup_autologin()
    setup_bootlogo()
    setup_bootsound()
    setup_graphic()

    copy_files(os.path.join(path_resources, "files"), user_files)
    copy_files(os.path.join(path_resources, "devicetree"), devicetree)

    for platform, path in default_devicetree_overlays.items():
        copy_files(path, os.path.join(devicetree, platform))

    shutil.copy(os.path.join(path_resources, "runshell.sh"), os.path.join(path_temp_syslbuild, "files", "runshell.sh"))
    shutil.copy(os.path.join(path_resources, "preinit.sh"), os.path.join(path_temp_syslbuild, "files", "preinit.sh"))

    shutil.copy("gnuboxmaker/runshell_launcher.sh", os.path.join(path_temp_syslbuild, "files", "runshell_launcher.sh"))
    shutil.copy("gnuboxmaker/run_session_wayland.sh", os.path.join(path_temp_syslbuild, "files", "run_session_wayland.sh"))
    shutil.copy("gnuboxmaker/run_session_x11.sh", os.path.join(path_temp_syslbuild, "files", "run_session_x11.sh"))
    shutil.copy("gnuboxmaker/system_preinit.sh", os.path.join(path_temp_syslbuild, "files", "system_preinit.sh"))
    shutil.copy("gnuboxmaker/system_init_hook.sh", os.path.join(path_temp_syslbuild, "files", "system_init_hook.sh"))

    if current_project.allow_updatescript and current_project.separate_data_partition:
        shutil.copy("gnuboxmaker/self_update.sh", os.path.join(path_temp_syslbuild, "files", "self_update.sh"))
        shutil.copy("gnuboxmaker/updatescript.sh", os.path.join(path_temp_syslbuild, "files", "updatescript.sh"))

    prepair_devicetree(devicetree)

def copy_bins(name, output_name=None):
    if output_name is None: output_name = name
    output_path = os.path.join(path_temp_syslbuild, output_name)
    deleteAny(output_path)
    buildExecute(["cp", "-a", os.path.join("gnuboxmaker", name) + "/.", output_path])

def setup_write_bins(builditems):
    copy_bins("kernel_build/output", "kernel_image")
    copy_bins("blobs")

    directories = []

    # ---------------------- x86_64
    items = [
        ["rootfs directory x2", "."],
        ["kernel_image/amd64/kernel_modules", "/usr"],
        ["kernel_image/amd64/kernel.img", "/kernel.img", [0, 0, "0644"]]
    ]

    # ЧТО ТУТ БЛЯТЬ С ПРАВАМИ ДОСТУПА. БЕЗ ЭТОЙ ХУЙНЮ НИХУЯ НЕ ПАШЕТ
    # походу при копировании plymouth проставляет права доступа другим директориям а без этого мы получаем жопу и не поднимающийся dbus
    if current_project.boot_splash or True:
        directories.append(["/var/lib/plymouth", [0, 0, "0755"]])
        directories.append(["/var/spool/plymouth", [0, 0, "0755"]])
        directories.append(["/run/plymouth", [0, 0, "0755"]])
        items.append(["blobs/embedded-plymouth/x86_64", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["amd64"],

        "type": "directory",
        "name": "rootfs directory x3",
        "export": False,

        "items": items,
        "directories": directories
    })

    # ---------------------- x86
    items = [
        ["rootfs directory x2", "."],
        ["kernel_image/i386/kernel_modules", "/usr"],
        ["kernel_image/i386/kernel.img", "/kernel.img", [0, 0, "0644"]]
    ]

    if current_project.boot_splash or True:
        items.append(["blobs/embedded-plymouth/x86", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["i386"],

        "type": "directory",
        "name": "rootfs directory x3",
        "export": False,

        "items": items,
        "directories": directories
    })

    # ---------------------- arm64
    items = [
        ["rootfs directory x2", "."]
    ]

    if current_project.export_img_opi_zero3:
        items.append(["kernel_image/arm64/opi_zero3/kernel_modules", "/usr"])
        items.append(["kernel_image/arm64/opi_zero3/firmware", "/usr/lib/firmware", [0, 0, "0644"]])

    if current_project.export_img_rpi_64:
        items.append(["kernel_image/arm64/rpi_64/kernel_modules", "/usr"])
        items.append(["kernel_image/arm64/rpi_5/kernel_modules", "/usr"])

    if current_project.boot_splash or True:
        items.append(["blobs/embedded-plymouth/arm64", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["arm64"],

        "type": "directory",
        "name": "rootfs directory x3",
        "export": False,

        "items": items,
        "directories": directories
    })

def setup_export_initramfs(builditems):
    if current_project.distro == "debian":
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

        if current_project.export_img_opi_zero3:
            builditems.append({
                "architectures": ["arm64"],

                "type": "debian-export-initramfs",
                "name": "initramfs_opi_zero3.img",
                "export": False,

                "kernel_config": "kernel_image/arm64/opi_zero3/kernel_config",
                "source": "rootfs directory x4"
            })

        if current_project.export_img_rpi_64:
            builditems.append({
                "architectures": ["arm64"],

                "type": "debian-export-initramfs",
                "name": "initramfs_rpi_64.img",
                "export": False,

                "kernel_version": "6.12.47-embedded-rpi-64+",
                "kernel_config": "kernel_image/arm64/rpi_64/kernel_config",
                "source": "rootfs directory x4"
            })

            builditems.append({
                "architectures": ["arm64"],

                "type": "debian-export-initramfs",
                "name": "initramfs_rpi_5.img",
                "export": False,

                "kernel_version": "6.12.47-embedded-rpi-5+",
                "kernel_config": "kernel_image/arm64/rpi_5/kernel_config",
                "source": "rootfs directory x4"
            })
    else:
        stop_error(f"unknown distro \"{current_project.distro}\"")

def getWaitFbStr(afterModules):
    if current_project.boot_splash:
        return "waitFbAfterModules" if afterModules else "waitFbBeforeModules"
    return ""

def setup_build_base(builditems):
    setup_build_distro(builditems)
    setup_write_files()

    items = [
        ["rootfs directory x1", "."],

        ["sprdwl_ng", "/etc/modules-load.d/sprdwl_ng.conf", [0, 0, "0644"], True],

        ["files/etc_config", "/etc", [0, 0, "0755"]],
        ["files/systemd_config", "/etc/systemd", [0, 0, "0755"]],
        ["files/runshell.sh", "/runshell.sh", [0, 0, "0755"]],
        ["files/runshell_launcher.sh", "/runshell_launcher.sh", [0, 0, "0755"]],
        ["files/preinit.sh", "/preinit.sh", [0, 0, "0755"]],
        ["files/system_preinit.sh", "/system_preinit.sh", [0, 0, "0755"]],

        ["custom_init.sh", "/usr/share/initramfs-tools/init", [0, 0, "0755"]],
        ["custom_init_hook.sh", "/etc/initramfs-tools/hooks/custom_init_hook.sh", [0, 0, "0755"]],
        ["files/system_init_hook.sh", "/etc/initramfs-tools/hooks/system_init_hook.sh", [0, 0, "0755"]],

        ["files/user_files", "/", [0, 0, "0755"]],
    ]

    if current_project.allow_updatescript and current_project.separate_data_partition:
        items.append(["files/self_update.sh", "/self_update.sh", [0, 0, "0755"]])
        items.append(["files/updatescript.sh", "/updatescript.sh", [0, 0, "0755"]])

    if current_project.boot_sound == "init" or (current_project.boot_sound == "logo" and current_project.boot_splash):
        items.append(["files/startup.wav", "/startup.wav", [0, 0, "0644"]])

    if current_project.integrate_liamounts:
        items.append(["liamounts", "/liamounts", [0, 0, "0755"]])

    directories = []

    if current_project.session_mode == "wayland":
        items.append(["files/run_session_wayland.sh", "/run_session.sh", [0, 0, "0755"]])
    elif current_project.session_mode == "x11":
        items.append(["files/run_session_x11.sh", "/run_session.sh", [0, 0, "0755"]])
    elif current_project.session_mode == "tty":
        directories.append(["/.session_mode_tty", [0, 0, "0000"]])

    builditem = {
        "type": "directory",
        "name": "rootfs directory x2",
        "export": False,

        "directories": directories,
        "items": items,
        "delete": []
    }

    if current_project.boot_splash:
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

    directories = [
        ["/bootmnt", [0, 0, "0755"]]
    ]

    if current_project.separate_data_partition:
        directories.append(["/data", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["amd64", "i386"],

        "type": "directory",
        "name": "rootfs directory x5",
        "export": False,

        "items": [
            ["rootfs directory x4", "."],
            ["initramfs.img", "/initramfs.img", [0, 0, "0644"]]
        ],

        "directories": directories
    })

    builditems.append({
        "architectures": ["arm64"],

        "type": "directory",
        "name": "rootfs directory x5",
        "export": False,

        "items": [
            ["rootfs directory x4", "."]
        ],

        "directories": directories
    })

    builditems.append({
        "type": "filesystem",
        "name": "rootfs.img",
        "export": False,

        "source": "rootfs directory x5",

        "fs_type": "ext4",
        "size": current_project.size_root_partition, 
        "minsize": current_project.minsize_root_partition,
        "label": "rootfs"
    })

def export_rpi_64(builditems, cmdline, appendPartitions):
    config_txt = f"""# For more options and information see
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
"""

    override = get_devicetree_override("rpi_64")
    if override:
        config_txt += f"\ndevice_tree={override}.dtb"

    overlays = get_devicetree_overlays("rpi_64")
    for overlay in overlays:
        config_txt += f"\ndtoverlay={overlay}"

    writeText(os.path.join(path_temp_syslbuild, "files", "cmdline_rpi_64.txt"), exclude_string("root=/dev/mmcblk0p2 " + cmdline + f" {getWaitFbStr(True)}\n", current_project.exclude_cmdline))
    writeText(os.path.join(path_temp_syslbuild, "files", "config_rpi_64.txt"), config_txt)

    builditems.append({
        "architectures": ["arm64"],

        "type": "gitclone",
        "name": "rpi_64_firmware",
        "export": False,

        "git_url": "https://github.com/raspberrypi/firmware",
        "git_branch": "master",
        "git_checkout": "1.20250915"
    })

    items = [
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

        ["kernel_image/arm64/rpi_5/boot", "/"],
        ["kernel_image/arm64/rpi_5/kernel.img", "/kernel_2712.img"],
        ["kernel_image/arm64/rpi_5/kernel_config", "/kernel2712_config"],
        ["initramfs_rpi_5.img", "/initramfs_2712"],

        ["files/cmdline_rpi_64.txt", "/cmdline.txt"],
        ["files/config_rpi_64.txt", "/config.txt"]
    ]

    dtbList = devicetree_get_files("rpi_64", "dtb")
    for dtb in dtbList:
        items.append([dtb, f"/{os.path.basename(dtb)}"])

    dtboList = devicetree_get_files("rpi_64", "dtbo")
    for dtbo in dtboList:
        items.append([dtbo, f"/overlays/{os.path.basename(dtbo)}"])

    builditems.append({
        "architectures": ["arm64"],

        "type": "directory",
        "name": "boot_rpi_64",
        "export": False,

        "items": items,

        "directories": [
            ["/rpi_64", [0, 0, "0000"]]
        ]
    })

    builditems.append({
        "architectures": ["arm64"],

        "type": "filesystem",
        "name": "boot_rpi_64.img",
        "export": False,

        "source": "boot_rpi_64",

        "fs_type": "fat32",
        "size": current_project.size_boot_partition,
        "minsize": current_project.minsize_boot_partition,
        "label": "BOOT"
    })

    builditems.append({
        "architectures": ["arm64"],

        "type": "full-disk-image",
        "name": f"{current_project_name} RPI 64.img",
        "export": True,

        "size": "auto + (10 * 1024 * 1024)",

        "partitionTable": "dos",
        "partitions": [
            ["boot_rpi_64.img", "c"],
            ["rootfs.img", "linux"]
        ] + appendPartitions
    })

def export_opi_zero3(builditems, cmdline, appendPartitions):
    dtboList_active = []
    for overlay in get_devicetree_overlays("opi_zero3"):
        dtboList_active.append(overlay + ".dtbo")

    devicetree = get_devicetree_override("opi_zero3")
    if devicetree:
        devicetree = devicetree + ".dtb"
    else:
        devicetree = "sun50i-h618-orangepi-zero3.dtb"

    builditems.append({
        "architectures": ["arm64"],

        "type": "singleboard",
        "name": f"{current_project_name} OPI ZERO 3.img",
        "export": True,

        "singleboardType": "uboot-offset",

        "bootloader": "blobs/u-boot-sunxi-with-spl.bin",
        "bootloader_offset": 16,
        "bootloaderDtb": devicetree,
        "dtbList": [
            "kernel_image/arm64/opi_zero3/sun50i-h618-orangepi-zero3.dtb"
        ] + devicetree_get_files("opi_zero3", "dtb"),
        "dtboList": devicetree_get_files("opi_zero3", "dtbo"),
        "dtboList_active": dtboList_active,

        "trigger_boot_flag": "opi_zero3",

        "kernel": "kernel_image/arm64/opi_zero3/kernel.img",
        "initramfs": "initramfs_opi_zero3.img",
        "rootfs": "rootfs.img",
        "appendPartitions": appendPartitions,

        "boot_partition_size": current_project.size_boot_partition,
        "boot_partition_minsize": current_project.minsize_boot_partition,
        "boot_partition_name": "BOOT",

        "kernel_args_auto": True,
        "kernel_rootfs_auto": "manual",
        "kernel_args": exclude_string(cmdline + f" cma=512M {getWaitFbStr(False)}", current_project.exclude_cmdline) # why is "waitFbBeforeModules" here? because in this FUCKING Chinese board, half of the peripherals start with a fucking delay, and it should be initialized by the time plymouth is launched
    })

def setup_build_targets(builditems, cmdline):
    appendPartitions = []

    if current_project.separate_data_partition:
        builditems.append({
            "type": "filesystem",
            "name": "data.img",
            "export": False,

            "fs_type": "ext4",
            "size": current_project.minsize_data_partition,
            "label": "DATA",

            "chmod": [
                ["/", "1777", False]
            ],

            "chown": [
                ["/", 0, 0, False]
            ]
        })
        appendPartitions.append(["data.img", "linux"])

    if current_project.export_img_bios_mbr:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{current_project_name} BIOS MBR.img",
            "export": True,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "dos",
            "partitions": [
                ["rootfs.img", "linux"]
            ] + appendPartitions,

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

    if current_project.export_img_bios_gpt or current_project.export_img_bios_and_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "filesystem",
            "name": "bios boot.img",
            "export": False,

            "size": "1M"
        })

    if current_project.export_img_bios_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{current_project_name} BIOS GPT.img",
            "export": True,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["bios boot.img", "bios"],
                ["rootfs.img", "linux"]
            ] + appendPartitions,

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

    if current_project.export_img_uefi_gpt or current_project.export_img_bios_and_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "filesystem",
            "name": "uefi boot.img",
            "export": False,

            "fs_arg": "-F32",
            "fs_type": "fat",
            "size": current_project.size_efi_partition,
            "label": "EFI",

            "minsize": current_project.minsize_efi_partition
        })

    if current_project.export_img_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{current_project_name} UEFI GPT.img",
            "export": True,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["uefi boot.img", "efi"],
                ["rootfs.img", "linux"]
            ] + appendPartitions,

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

    if current_project.export_img_bios_and_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{current_project_name} BIOS UEFI GPT.img",
            "export": True,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["uefi boot.img", "efi"],
                ["bios boot.img", "bios"],
                ["rootfs.img", "linux"]
            ] + appendPartitions,

            "bootloader": {
                "type": "grub",
                "config": "grub.cfg",
                "esp": 0,
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

    if current_project.export_img_opi_zero3:
        export_opi_zero3(builditems, cmdline, appendPartitions)

    if current_project.export_img_rpi_64:
        export_rpi_64(builditems, cmdline, appendPartitions)

def generate_syslbuild_project():
    cmdline_console = ""

    exclude_tty1_from_consoles = current_project.exclude_tty1_from_consoles or (current_project.exclude_tty1_from_consoles_in_quiet and current_project.boot_quiet)

    if not exclude_tty1_from_consoles and not current_project.make_tty1_primary_console:
        cmdline_console = " console=tty1"

    if current_project.uartlogs:
        cmdline_console += f" console=ttyS0,{current_project.uartlogs_speed}"

    if not exclude_tty1_from_consoles and current_project.make_tty1_primary_console:
        cmdline_console = " console=tty1"

    if cmdline_console == "":
        # for some reason, console=null causes the linux userspace to freeze completely. it will be necessary to develop a kernel module, something like dummy_console (it turns out that there is a built-in ttynull)
        # cmdline_console = "console=null"

        # crutch
        # cmdline_console = "console=ttyS0,115200"

        # I still found a working way to completely get rid of the logs using the built-in linux method. however, this requires enabling CONFIG_NULL_TTY in the kernel config.
        cmdline_console = "console=ttynull"

    cmdline = f"{"ro" if current_project.root_readonly else "rw"} rootwait=60 systemd.getty_auto=0 selinux=0 plymouth.ignore-serial-consoles mount_bootmnt {cmdline_console} preinit=/root/system_preinit.sh {current_project.cmdline}"

    if current_project.boot_sound == "init":
        cmdline += " startupsound_afterMountRoot=/startup.wav"
    
    if current_project.boot_sound == "logo" and current_project.boot_splash:
        cmdline += " startupsound_afterLogoShow=/startup.wav"

    if current_project.var_is_temp and not (current_project.separate_data_partition and current_project.separate_data_partition_var_link):
        cmdline += " makevartmp"

    if current_project.root_expand and not current_project.separate_data_partition:
        cmdline += " root_processing root_expand"

    if current_project.separate_data_partition:
        cmdline += " mount_data"

        if current_project.separate_data_partition_home_link:
            cmdline += " home_link"

        if current_project.separate_data_partition_var_link:
            cmdline += " var_link"

        if current_project.separate_data_partition_etc_link:
            cmdline += " etc_link"

    if current_project.allow_updatescript:
        cmdline += " allow_updatescript while_after_updatescript_crash"
        
        if not current_project.use_separate_splash_for_update:
            cmdline += " updatescript_state_not_need_in_plymouth"

    if current_project.boot_splash:
        cmdline += f" minlogotime={current_project.minlogotime}"

    if current_project.boot_quiet:
        cmdline += f" systemd.show_status=false rd.systemd.show_status=false systemd.log_target=journal rd.systemd.log_target=journal udev.log_level=1 rd.udev.log_level=1 systemd.log_level=emerg rd.systemd.log_level=emerg clear noCursorBlink vt.global_cursor_default=0 quiet loglevel=0"

    boot_splash_substring = " splash earlysplash"
    if current_project.boot_splash:
        cmdline += boot_splash_substring

    if current_project.session_mode == "init":
        cmdline += " init=/runshell.sh"

    session_mode = current_project.session_mode
    if session_mode != "x11" and session_mode != "wayland" and current_project.screen_idle_time > 0:
        cmdline += f" consoleblank={current_project.screen_idle_time}"

    architectures = []
    builditems = []

    deleteAny(os.path.join(path_temp_syslbuild, "files"))
    deleteAny(os.path.join(path_temp_syslbuild, "chroot"))
    deleteAny(os.path.join(path_temp_syslbuild, "kernel_image"))
    deleteAny(os.path.join(path_temp_syslbuild, "blobs"))
    
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

    cmdline = exclude_string(cmdline, current_project.exclude_cmdline)

    with open(os.path.join(path_temp_syslbuild, "grub.cfg"), "w") as f:
        grubcfg = f"""set cmdline="{cmdline}" """

        if current_project.dont_use_splash_on_efi:
            grubcfg += "\n"
            grubcfg += f"""if [ "$grub_platform" = "efi" ]; then
    set cmdline="{cmdline.replace(boot_splash_substring, "")}"
fi"""


        grubcfg += "\n"
        grubcfg += f"""probe --set root_fs_uuid --fs-uuid $root
linux /kernel.img root=UUID=$root_fs_uuid ${{cmdline}}
initrd /initramfs.img
boot"""

        f.write(grubcfg)

def run_syslbuild():
    cmd_base = [
        "bash", "-c",
        f"cd {path_temp_syslbuild!r} && {sys.executable!r} {os.path.abspath('syslbuild.py')!r} "
        f"--arch ALL {path_temp_syslbuild_file!r} "
        f"--temp {os.path.join(current_project_directory, '.temp')!r} "
        f"--output {os.path.join(current_project_directory, 'output')!r} "
        f"--lastlog {os.path.join(current_project_directory, 'last.log')!r}"
    ]

    if os.geteuid() != 0:
        if guiLoaded:
            cmd = ["pkexec"] + cmd_base
        else:
            cmd = ["sudo"] + cmd_base
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

def init_devicetree(name):
    devicetree = os.path.join(path_resources, "devicetree", name)

    os.makedirs(devicetree, exist_ok=True)

    devicetree_override = os.path.join(devicetree, "override.txt")
    if not os.path.isfile(devicetree_override):
        with open(devicetree_override, "w", encoding="utf-8") as f:
            pass

    devicetree_overlays = os.path.join(devicetree, "overlays.txt")
    if not os.path.isfile(devicetree_overlays):
        with open(devicetree_overlays, "w", encoding="utf-8") as f:
            pass

def update_project_structure():
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

    logo_path_png = os.path.join(path_resources, "logo.png")
    logo_path_gif = os.path.join(path_resources, "logo.gif") # gif на экране загрузки еще не реализован
    if not os.path.isfile(logo_path_png) and not os.path.isfile(logo_path_gif):
        copyFile(logo_path_png, "gnuboxmaker.png")

    logo_updating_path_png = os.path.join(path_resources, "logo_updating.png")
    logo_updating_path_gif = os.path.join(path_resources, "logo_updating.gif")
    if not os.path.isfile(logo_updating_path_png) and not os.path.isfile(logo_updating_path_gif):
        copyFile(logo_updating_path_png, "gnuboxmaker/logo_updating.png")

    startup_sound = os.path.join(path_resources, "startup.wav")
    if not os.path.isfile(startup_sound):
        copyFile(startup_sound, "gnuboxmaker/startup.wav")

    gitignore_path = os.path.join(current_project_directory, ".gitignore")
    if not os.path.isfile(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("output\n")
            f.write(".temp\n")
            f.write("last.log\n")

    init_devicetree("opi_zero3")
    init_devicetree("rpi_64")

def load_project(path):
    global current_project
    global current_project_name
    global current_project_directory
    global path_temp
    global path_resources
    global path_temp_syslbuild
    global path_temp_syslbuild_file

    if os.path.isfile(path):
        current_project = raw_load_project(path)
        version_diff = checkVersion(current_project)
        if version_diff > 0:
            show_error(f"you have the syslbuild {syslbuild.formatVersion(syslbuild.VERSION)} version, while the project was saved in a newer version of {syslbuild.formatVersion(current_project.gnubox_version)}")
            return False
        elif version_diff < 0:
            current_project.gnubox_version = syslbuild.VERSION.copy()
            raw_save_project(path, current_project)
        else:
            current_project.gnubox_version = syslbuild.VERSION.copy()
    else:
        current_project = Project()
        current_project.gnubox_version = syslbuild.VERSION.copy()
        raw_save_project(path, current_project)

    current_project_directory = os.path.dirname(path)
    current_project_name = os.path.basename(current_project_directory)
    path_temp = os.path.join(current_project_directory, ".temp")
    path_resources = os.path.join(current_project_directory, "resources")
    path_temp_syslbuild = os.path.join(path_temp, "syslbuild")
    path_temp_syslbuild_file = os.path.join(path_temp_syslbuild, "project.json")

    update_project_structure()

    return True

# ---------------------------------------- console build

guiLoaded = False
if len(sys.argv) > 1:
    if load_project(sys.argv[1]):
        build_project()
    sys.exit(0)

# ---------------------------------------- gui base

guiLoaded = True
window = tk.Tk()
window.title("Gnubox maker")
window.geometry("1200x700")

window.update_idletasks()
width = window.winfo_width()
height = window.winfo_height()
x = (window.winfo_screenwidth() // 2) - (width // 2)
y = (window.winfo_screenheight() // 2) - (height // 2)
window.geometry(f'{width}x{height}+{x}+{y}')

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
    if load_project(path):
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
