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
import version

# module_dir = os.path.join(os.path.dirname(__file__), "gnuboxmaker/pyimport")

gnuboxmaker_dir = os.path.join(os.getcwd(), "gnuboxmaker")
module_dir = os.path.join(gnuboxmaker_dir, "pyimport")

sys.path.insert(0, module_dir)

# ---------------------------------------- data

HandleKey_varians = ["ignore", "poweroff", "reboot", "suspend", "hibernate", "lock"] # halt, kexec
session_user_variants = ["user", "root"]
session_mode_variants = ["wayland", "x11", "tty", "init"]
weston_shell_variants = ["kiosk", "desktop"]
splash_mode_variants = ["center", "fill", "contain", "cover"]
boot_sound_variants = ["none", "init", "logo"]

QUIET_AGETTY = "--noreset --nohostname --nohints --nonewline --noclear --skip-login --noissue"
RIGHTS_644_755 = [[0, 0, "0644"], [0, 0, "0755"]]

default_debian_suite = "trixie"
default_debian_snapshot = "http://snapshot.debian.org/archive/debian/20260217T143331Z"
default_value = "<default>"
github_user = "igorkll"

@dataclass
class Project:
    gnubox_version: list[int] = field(default_factory=lambda: [0, 0, 0])

    distro: str = "debian"
    user_packages: list[str] = field(default_factory=list)
    exclude_packages: list[str] = field(default_factory=list)
    
    debian_variant: str = "minbase"
    debian_suite: str = default_value
    debian_snapshot: str = default_value

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

    enable_echo: bool = False
    enable_cursor: bool = False

    uartlogs: bool = False
    uartlogs_speed: int = 115200
    uartlogs_login: bool = False
    uartlogs_rootshell: bool = False

    root_login_unlock: bool = False
    password_root: str = ""
    password_user: str = ""
    
    exclude_tty1_from_consoles: bool = False
    exclude_tty1_from_consoles_in_quiet: bool = True
    make_tty1_primary_console: bool = False

    splash_bg: str = "0, 0, 0"
    splash_updating_bg: str = "0, 0, 0"
    splash_mode: str = "contain"
    splash_scale: float = 0.7
    use_separate_splash_for_update: bool = True

    timezone: str = "UTC" # example: Europe/Moscow
    rtc_mode: str = "UTC" # UTC / LOCAL

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
    integrate_super_kiosk_browser: bool = False

    integrate_xwayland: bool = True
    integrate_firmwares: bool = True
    integrate_armbian_firmwares_if_need: bool = True
    integrate_raspberry_firmwares_if_need: bool = True
    integrate_bluetooth: bool = True
    integrate_network: bool = True
    integrate_network_resolved: bool = True
    integrate_network_timesync: bool = True
    integrate_network_wifi: bool = True
    integrate_audio: bool = True
    integrate_advanced_gpu_packages: bool = True

    wifi_autoconnect_name: str = ""
    wifi_autoconnect_password: str = ""
    wifi_autoconnect_security: str = "wpa-psk"

    plymouth_disable_esc_button: bool = True

    export_x86_64: bool = True
    export_x86: bool = False
    export_arm64: bool = False
    export_arm: bool = False
    export_armel: bool = False

    export_img_bios_mbr: bool = False
    export_img_bios_gpt: bool = False
    export_img_uefi_gpt: bool = False
    export_img_bios_and_uefi_gpt: bool = True

    export_img_opi_zero3: bool = False
    export_img_rpi_32_armel: bool = False
    export_img_rpi_32: bool = False
    export_img_rpi_64: bool = False

    export_rootfs_directory: bool = False
    export_rootfs_tar_gz: bool = False
    export_rootfs_tar_xz: bool = False
    export_rootfs_tar: bool = False

    platform_opi_zero3_cma: str = "256M"
    platform_opi_zero3_hdmi_audio_high_priority: bool = True

    rebranding_enabled: bool = True
    rebranding_issue: str = "gnubox \\n \\l\n\n"
    rebranding_issue_net: str = "gnubox\n"
    rebranding_motd: str = ""
    rebranding_os_release_name: str = "Gnubox"
    rebranding_os_release_id: str = "gnubox"
    rebranding_remove_debian_logos: bool = True

# ---------------------------------------- functions

class CancelGUI(Exception):
    pass

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

# ---------------------------------------- builder

current_project = None
current_project_name = None
current_project_directory = None

path_temp = None
path_resources = None
path_temp_syslbuild = None
path_temp_syslbuild_file = None

def get_kernel_path(architecture, filtername):
    if architecture == "amd64" or architecture == "i386":
        return f"gnuboxmaker/kernel_build/output/{architecture}"
    
    return f"gnuboxmaker/kernel_build/output/{architecture}/{filtername}"

def request_kernel(builditems, architecture, filtername):
    working_dir = os.path.dirname(os.path.abspath(__file__))
    kernel_dir = os.path.join(working_dir, get_kernel_path(architecture, filtername))

    buildLog(f"request kernel: {architecture} {filtername}")
    buildLog(f"working dir: {working_dir}")
    buildLog(f"kernel dir: {kernel_dir}")

    if os.path.isdir(kernel_dir):
        return

    kernel_build_dir = "gnuboxmaker/kernel_build"
    
    cmd = f"cd {kernel_build_dir!r} && {sys.executable!r} {os.path.abspath('syslbuild.py')!r} --filters {filtername} --arch {architecture} kernel_build.json"

    builditems.insert(0, {
        "type": "execute-commands",
        "name": f"request_kernel_{architecture}_{filtername}",

        "working_dir": working_dir,
        "disable_cache": True,

        "commands": [
            cmd
        ]
    })

def setup_build_architectures(builditems, architectures):
    build_rpi64_kernel = False
    build_rpi32_kernel = False

    

    if current_project.export_x86_64:
        architectures.append("amd64")
        request_kernel(builditems, "amd64", "x86")

    if current_project.export_x86:
        architectures.append("i386")
        request_kernel(builditems, "i386", "x86")

    if current_project.export_arm64:
        architectures.append("arm64")
        
        if current_project.export_img_opi_zero3:
            request_kernel(builditems, "arm64", "sunxi")

        if current_project.export_img_rpi_64:
            build_rpi64_kernel = True
            request_kernel(builditems, "arm64", "rpi_5")

    if current_project.export_arm:
        architectures.append("armhf")
        if current_project.export_img_rpi_32:
            build_rpi64_kernel = True
            build_rpi32_kernel = True

    if current_project.export_armel:
        architectures.append("armel")
        if current_project.export_img_rpi_32_armel:
            build_rpi64_kernel = True
            build_rpi32_kernel = True
    

    if build_rpi64_kernel:
        request_kernel(builditems, "arm64", "rpi_64")

    if build_rpi32_kernel:
        request_kernel(builditems, "armhf", "rpi_kernel")
        request_kernel(builditems, "armhf", "rpi_kernel7")

def setup_user_password(user, password):
    if len(password) == 0:
        return f"passwd -d {user}"
    else:
        return f"echo \"{user}:{password}\" | chpasswd"

def gen_default_first_chroot_script():
    if current_project.session_mode == "wayland" or current_project.session_mode == "x11":
        user_shell = "/gnubox/run_session.sh"
    else:
        user_shell = "/gnubox/runshell_launcher.sh"
        
    aaa_setup = f"""#!/bin/bash

# ------------

ln -sf /usr/share/zoneinfo/{current_project.timezone} /etc/localtime

cat > /etc/adjtime <<'EOF'
0.0 0 0.0
0
{current_project.rtc_mode}
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

systemctl set-default graphical.target

# ------------

usermod -s {user_shell} root
useradd -m -u 10000 -s {user_shell} user
usermod -aG video,input,audio,render user
mkdir -p -m 700 /home/user
chown user:user /home/user"""

    if current_project.root_login_unlock:
        aaa_setup += "\npasswd -u root"

    aaa_setup += "\n" + setup_user_password("root", current_project.password_root)
    aaa_setup += "\n" + setup_user_password("user", current_project.password_user)

    aaa_setup += "\n"

    if current_project.boot_splash:
        aaa_setup += "\n" + f"""plymouth-set-default-theme bootlogo
cp -f /usr/share/plymouth/themes/bootlogo/bootlogo.plymouth /usr/share/plymouth/themes/default.plymouth"""

        if current_project.plymouth_disable_esc_button:
            aaa_setup += "\n" + f"""# this trash break systemd quiet
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

    if current_project.uartlogs_login or current_project.uartlogs_rootshell:
        zzz_setup += "\n\nsystemctl enable uartshell.service"

    zzz_setup += "\n\ntouch /.chrootend"

    return zzz_setup

def gen_last_non_systemd_script():
    last_setup = "#!/bin/bash\n"

    if current_project.integrate_network and current_project.integrate_network_resolved:
        last_setup += "\n" + f"""rm -f /etc/resolv.conf
ln -s /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf

cat > /etc/NetworkManager/conf.d/90-dns-systemd-resolved.conf <<'EOF'
[main]
dns=systemd-resolved
EOF
"""

    if current_project.integrate_network and current_project.integrate_network_wifi and current_project.wifi_autoconnect_name:
        name = current_project.wifi_autoconnect_name
        password = current_project.wifi_autoconnect_password
        security = current_project.wifi_autoconnect_security

        nmcli_cmd = f"nmcli --offline connection add type wifi con-name \"{name}\" ifname wlan0 ssid \"{name}\""

        if security == 'wpa-psk' and password:
            nmcli_cmd += f' wifi-sec.key-mgmt wpa-psk wifi-sec.psk "{password}"'
        elif security == 'sae' and password:
            nmcli_cmd += f' wifi-sec.key-mgmt sae wifi-sec.psk "{password}"'
        elif security == 'owe':
            nmcli_cmd += ' wifi-sec.key-mgmt owe'
        else:
            nmcli_cmd += ' wifi-sec.key-mgmt none'
        
        connection_file = f"/etc/NetworkManager/system-connections/{name}.nmconnection"
        last_setup += f"\n{nmcli_cmd} > {connection_file}"
        last_setup += f"\nchmod 600 {connection_file}"
        last_setup += f"\nchown root:root {connection_file}"

    return last_setup

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

    scripts.append([f"linux-embedded-setup-scripts/disable_shutdown_reboot_cmd_wall_messages.sh", False, False])

    for f in sorted(Path(chroot_project_directory).iterdir(), key=lambda p: p.name):
        if f.is_file():
            scripts.append(f"chroot/{f.name}")
            shutil.copy(
                os.path.join(chroot_project_directory, f.name),
                os.path.join(chroot_scripts_directory, f.name)
            )

    scripts.append([f"files/fix.sh", False, False])

    scripts.append([f"chroot/last_setup.sh", False, False])
    with open(os.path.join(chroot_scripts_directory, "last_setup.sh"), "w") as f:
        f.write(gen_last_non_systemd_script())

    scripts.append([f"files/cleanup_after_firstboot.sh", False, False])

    return scripts

def get_t64_suffix(debian_suite, for64bits):
    if debian_suite == "sid" or (debian_suite == "trixie" and not for64bits):
        return "t64"
    
    return ""

def add_for_architectures(includeList, packageName, architectures, architecture):
    if architectures is None or architecture in architectures:
        includeList.append(packageName)

def setup_build_debian(builditems, for64bits, architecture):
    include = [
        "initramfs-tools",

        "systemd",
        "systemd-sysv",

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
        "jq"
    ]

    debian_suite = current_project.debian_suite
    debian_snapshot = current_project.debian_snapshot

    if debian_suite == default_value:
        debian_suite = default_debian_suite

    if debian_snapshot == default_value:
        debian_snapshot = default_debian_snapshot

    if current_project.sudo_privileges:
        include.append("sudo")

    if current_project.integrate_audio:
        include.append("pipewire")
        include.append("pipewire-pulse")
        include.append("pipewire-alsa")
        include.append("wireplumber")
        include.append("libspa-0.2-modules")
        include.append("alsa-utils")
        include.append("libpulse0")
        include.append("rtkit")
        include.append("libasound2" + get_t64_suffix(debian_suite, for64bits))

    wifiless_packages = False

    if current_project.integrate_bluetooth:
        wifiless_packages = True
        include.append("bluez")
        include.append("bluetooth")

    if current_project.integrate_firmwares:
        include.append("firmware-linux")

    if current_project.integrate_network:
        include.append("network-manager")
        include.append("iproute2")
        include.append("ca-certificates")

        if current_project.integrate_network_resolved:
            include.append("systemd-resolved")

        if current_project.integrate_network_timesync:
            include.append("systemd-timesyncd")

        if current_project.integrate_network_wifi:
            wifiless_packages = True
            include.append("wpasupplicant")

    if wifiless_packages:
        if current_project.integrate_firmwares:
            include.append("firmware-realtek")
            include.append("firmware-brcm80211")
        
        include.append("rfkill")
        include.append("wireless-regdb")
        include.append("iw")

    if current_project.boot_splash:
        include.append("plymouth") # install basic plymouth files. The part will later be replaced by embedded plymouth.
        include.append("plymouth-themes")

    if current_project.session_mode == "wayland" or current_project.session_mode == "x11":
        include.append("mesa-utils")
        include.append("libgl1-mesa-dri")
        include.append("libgbm1")
        include.append("libdrm2")

        if debian_suite == "trixie" or debian_suite == "sid":
            include.append("libegl1")
        else:
            include.append("libegl1-mesa")

        if current_project.integrate_advanced_gpu_packages:
            add_for_architectures(include, "mesa-vulkan-drivers", None, architecture)
            add_for_architectures(include, "intel-media-va-driver-non-free", ["amd64", "i386"], architecture)
            add_for_architectures(include, "mesa-va-drivers", None, architecture)
            add_for_architectures(include, "mesa-vdpau-drivers", None, architecture)
            add_for_architectures(include, "libva2", None, architecture)
            add_for_architectures(include, "libva-drm2", None, architecture)
            add_for_architectures(include, "libvdpau1", None, architecture)

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
    include = remove_duplicates(include)

    item = {
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
        "suite": debian_suite,
        "url": debian_snapshot
    }

    item["architectures"] = [architecture]

    builditems.append(item)

def setup_build_distro(builditems):
    if current_project.distro == "debian":
        setup_build_debian(builditems, True, "amd64")
        setup_build_debian(builditems, True, "arm64")
        setup_build_debian(builditems, False, "i386")
        setup_build_debian(builditems, False, "armhf")
        setup_build_debian(builditems, False, "armel")
    else:
        stop_error(f"unknown distro \"{current_project.distro}\"")

def setup_download(builditems):
    def addDownload(name, version):
        builditems.append({
            "type": "gitclone",
            "name": name,
            "export": False,

            "git_url": f"https://github.com/{github_user}/{name}",
            "git_checkout": version
        })

    def addDownloadRelease(reponame, version, filename):
        builditems.append({
            "type": "download",
            "name": filename,
            "export": False,

            "url": f"https://github.com/{github_user}/{reponame}/releases/download/{version}/{filename}",
        })

    def unpackRelease(archive):
        builditems.append({
            "type": "unpack-tar-auto",
            "name": get_name_without_all_extensions(archive),
            "export": False,

            "archive": archive
        })

    if current_project.integrate_armbian_firmwares_if_need:
        builditems.append({
            "architectures": ["arm64"],

            "type": "gitclone",
            "name": "armbian_firmware",
            "export": False,

            "git_url": "https://github.com/armbian/firmware",
            "git_checkout": "d9846710f54da5e4383e2d67311819659ac2cf5c"
        })

    if current_project.integrate_super_kiosk_browser:
        builditems.append({
            "type": "unpack-archive",
            "name": "super-kiosk-browser-unpacked",
            "export": False,

            "archive": "super_kiosk_browser_build.zip"
        })

        builditems.append({
            "architectures": ["amd64"],

            "type": "from-directory",
            "name": "super-kiosk-browser-target",
            "export": False,

            "source": "super-kiosk-browser-unpacked",
            "path": "/super_kiosk_browser_build/super_kiosk_browser-linux-x64"
        })

        builditems.append({
            "architectures": ["arm64"],

            "type": "from-directory",
            "name": "super-kiosk-browser-target",
            "export": False,

            "source": "super-kiosk-browser-unpacked",
            "path": "/super_kiosk_browser_build/super_kiosk_browser-linux-arm64"
        })

    addDownload("custom-debian-initramfs-init", "1.6.6")
    addDownload("linux-embedded-setup-scripts", "0.2")
    addDownloadRelease("linux-bootloaders", "1.2", "linux-bootloaders.tar.gz")
    unpackRelease("linux-bootloaders.tar.gz")

    if current_project.integrate_liamounts:
        addDownload("liamounts", "2.1")

    if current_project.integrate_super_kiosk_browser:
        addDownloadRelease("super-kiosk-browser", "1.1", "super_kiosk_browser_build.zip")

    if current_project.boot_splash and current_project.plymouth_disable_esc_button:
        addDownload("embedded-plymouth", "1.2")
    
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

    if current_project.uartlogs_login or current_project.uartlogs_rootshell:
        autologin_str = ""
        if not current_project.uartlogs_login:
            autologin_str = f"{QUIET_AGETTY} --autologin root "

        content = f"""[Unit]
Description=rootshell on UART
After=multi-user.target

[Service]
Type=idle
ExecStart=-/sbin/agetty {autologin_str}ttyS0 {current_project.uartlogs_speed} vt102
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
path=/gnubox/runshell_launcher.sh
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
        xinitrc += "\n/gnubox/runshell_launcher.sh"

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

def setup_write_files():
    etc_config = os.path.join(path_temp_syslbuild, "files", "etc_config")
    systemd_config = os.path.join(path_temp_syslbuild, "files", "systemd_config")
    user_files = os.path.join(path_temp_syslbuild, "files", "user_files")
    devicetree = os.path.join(path_temp_syslbuild, "files", "devicetree")
    user_initramfs = os.path.join(path_temp_syslbuild, "files", "user_initramfs")

    os.makedirs(etc_config, exist_ok=True)
    os.makedirs(systemd_config, exist_ok=True)
    os.makedirs(user_files, exist_ok=True)
    os.makedirs(devicetree, exist_ok=True)
    os.makedirs(user_initramfs, exist_ok=True)

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
    copy_files(os.path.join(path_resources, "initramfs"), user_initramfs)

    shutil.copy(os.path.join(path_resources, "runshell.sh"), os.path.join(path_temp_syslbuild, "files", "runshell.sh"))
    shutil.copy(os.path.join(path_resources, "preinit.sh"), os.path.join(path_temp_syslbuild, "files", "preinit.sh"))

    shutil.copy("gnuboxmaker/runshell_launcher.sh", os.path.join(path_temp_syslbuild, "files", "runshell_launcher.sh"))
    shutil.copy("gnuboxmaker/run_session_wayland.sh", os.path.join(path_temp_syslbuild, "files", "run_session_wayland.sh"))
    shutil.copy("gnuboxmaker/run_session_x11.sh", os.path.join(path_temp_syslbuild, "files", "run_session_x11.sh"))
    shutil.copy("gnuboxmaker/system_preinit.sh", os.path.join(path_temp_syslbuild, "files", "system_preinit.sh"))
    shutil.copy("gnuboxmaker/system_init_hook.sh", os.path.join(path_temp_syslbuild, "files", "system_init_hook.sh"))
    shutil.copy("gnuboxmaker/fix.sh", os.path.join(path_temp_syslbuild, "files", "fix.sh"))
    shutil.copy("gnuboxmaker/cleanup_after_firstboot.sh", os.path.join(path_temp_syslbuild, "files", "cleanup_after_firstboot.sh"))
    shutil.copy("gnuboxmaker/fix-rpi-x11.conf", os.path.join(path_temp_syslbuild, "files", "fix-rpi-x11.conf"))

    if current_project.allow_updatescript and current_project.separate_data_partition:
        shutil.copy("gnuboxmaker/self_update.sh", os.path.join(path_temp_syslbuild, "files", "self_update.sh"))
        shutil.copy("gnuboxmaker/updatescript.sh", os.path.join(path_temp_syslbuild, "files", "updatescript.sh"))

    prepair_devicetree(devicetree)

def copy_bins(name, output_name=None):
    if output_name is None: output_name = name
    output_path = os.path.join(path_temp_syslbuild, output_name)
    deleteAny(output_path)
    buildExecute(["cp", "-a", os.path.join("gnuboxmaker", name) + "/.", output_path])

def symlink_bins(name, output_name=None):
    if output_name is None:
        output_name = name
    output_path = os.path.join(path_temp_syslbuild, output_name)
    deleteAny(output_path)

    source_path = os.path.abspath(os.path.join("gnuboxmaker", name))
    os.symlink(source_path, output_path)

def setup_write_bins(builditems):
    symlink_bins("kernel_build/output", "kernel_image")
    symlink_bins("blobs")

    embedded_plymouth_base_path = "embedded-plymouth/release-binary/debian-bookworm-plymouth-22.02.122-patched"

    directories = [
        ["/usr", [0, 0, "0755"]]
    ]

    # ---------------------- x86_64

    items = [
        ["kernel_image/amd64/kernel_modules", "/usr", RIGHTS_644_755],
        ["kernel_image/amd64/kernel.img", "/kernel.img", [0, 0, "0644"]]
    ]

    if current_project.boot_splash and current_project.plymouth_disable_esc_button:
        items.append([f"{embedded_plymouth_base_path}/x86_64", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["amd64"],

        "type": "directory",
        "name": "rootfs directory overlay",
        "export": False,

        "items": items,
        "directories": directories
    })

    # ---------------------- x86
    items = [
        ["kernel_image/i386/kernel_modules", "/usr", RIGHTS_644_755],
        ["kernel_image/i386/kernel.img", "/kernel.img", [0, 0, "0644"]]
    ]

    if current_project.boot_splash and current_project.plymouth_disable_esc_button:
        items.append([f"{embedded_plymouth_base_path}/x86", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["i386"],

        "type": "directory",
        "name": "rootfs directory overlay",
        "export": False,

        "items": items,
        "directories": directories
    })

    # ---------------------- arm64
    items = []

    if current_project.boot_splash and current_project.plymouth_disable_esc_button:
        items.append([f"{embedded_plymouth_base_path}/arm64", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["arm64"],

        "type": "directory",
        "name": "rootfs directory overlay",
        "export": False,

        "items": items,
        "directories": directories
    })

    # ---------------------- armhf
    items = []

    if current_project.boot_splash and current_project.plymouth_disable_esc_button:
        items.append([f"{embedded_plymouth_base_path}/armhf", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["armhf"],

        "type": "directory",
        "name": "rootfs directory overlay",
        "export": False,

        "items": items,
        "directories": directories
    })

    # ---------------------- armel
    items = []

    if current_project.boot_splash and current_project.plymouth_disable_esc_button:
        items.append([f"{embedded_plymouth_base_path}/armel", "/", [0, 0, "0755"]])

    builditems.append({
        "architectures": ["armel"],

        "type": "directory",
        "name": "rootfs directory overlay",
        "export": False,

        "items": items,
        "directories": directories
    })

def getWaitFbStr(afterModules):
    if current_project.boot_splash:
        return "waitFbAfterModules" if afterModules else "waitFbBeforeModules"
    return ""

def rebranding(delete, directories, items):
    if current_project.rebranding_enabled:
        items.append([current_project.rebranding_issue, "/etc/issue", [0, 0, "0644"], True])
        items.append([current_project.rebranding_issue_net, "/etc/issue.net", [0, 0, "0644"], True])
        items.append([current_project.rebranding_motd, "/usr/share/base-files/motd", [0, 0, "0644"], True])
        items.append([current_project.rebranding_motd, "/etc/motd", [0, 0, "0644"], True])

        items.append([f"""NAME="{current_project.rebranding_os_release_name}"
ID="{current_project.rebranding_os_release_id}"
""", "/usr/lib/os-release", [0, 0, "0644"], True])

        if current_project.rebranding_remove_debian_logos:
            delete.append("/usr/share/pixmaps/debian-logo.png")
            delete.append("/usr/share/plymouth/debian-logo.png")

def setup_build_base(builditems, cmdline):
    setup_build_distro(builditems)
    setup_write_files()

    directories = [
        ["/bootmnt", [0, 0, "0755"]],

        ["/gnubox", [0, 0, "0755"]],
        ["/gnubox/user_initramfs", [0, 0, "0755"]],

        ["/usr", [0, 0, "0755"]],
        ["/usr/lib", [0, 0, "0755"]],
        ["/usr/lib/firmware", [0, 0, "0755"]],

        ["/usr/local", [0, 0, "0755"]],
        ["/usr/local/sbin", [0, 0, "0755"]]
    ]

    items = [
        ["rootfs directory x1", "."],

        [cmdline, "/gnubox/cmdline.txt", RIGHTS_644_755, True],

        ["files/etc_config", "/etc", RIGHTS_644_755],
        ["files/systemd_config", "/etc/systemd", RIGHTS_644_755],

        ["files/runshell.sh", "/gnubox/runshell.sh", [0, 0, "0755"]],
        ["files/runshell_launcher.sh", "/gnubox/runshell_launcher.sh", [0, 0, "0755"]],
        ["files/preinit.sh", "/gnubox/preinit.sh", [0, 0, "0755"]],
        ["files/system_preinit.sh", "/gnubox/system_preinit.sh", [0, 0, "0755"]],

        ["custom-debian-initramfs-init/custom_init.sh", "/usr/share/initramfs-tools/init", [0, 0, "0755"]],
        ["custom-debian-initramfs-init/custom_init_hook.sh", "/etc/initramfs-tools/hooks/custom_init_hook.sh", [0, 0, "0755"]],
        ["files/system_init_hook.sh", "/etc/initramfs-tools/hooks/system_init_hook.sh", [0, 0, "0755"]],

        ["files/user_files", "/", [0, 0, "0755"]],
        ["files/user_initramfs", "/gnubox/user_initramfs", [0, 0, "0755"]],
    ]

    if current_project.allow_updatescript and current_project.separate_data_partition:
        items.append(["files/self_update.sh", "/usr/local/sbin/self_update", [0, 0, "0755"]])
        items.append(["files/updatescript.sh", "/gnubox/updatescript.sh", [0, 0, "0755"]])

    if current_project.boot_sound == "init" or (current_project.boot_sound == "logo" and current_project.boot_splash):
        items.append(["files/startup.wav", "/gnubox/startup.wav", [0, 0, "0644"]])

    if current_project.integrate_liamounts:
        items.append(["liamounts", "/liamounts", [0, 0, "0755"]])

    if current_project.integrate_super_kiosk_browser:
        directories.append(["/gnubox/super_kiosk_browser", [0, 0, "0755"]])
        items.append(["super-kiosk-browser-target", "/gnubox/super_kiosk_browser", [0, 0, "0755"]])

    if current_project.session_mode == "wayland":
        items.append(["files/run_session_wayland.sh", "/gnubox/run_session.sh", [0, 0, "0755"]])
    elif current_project.session_mode == "x11":
        items.append(["files/run_session_x11.sh", "/gnubox/run_session.sh", [0, 0, "0755"]])
    elif current_project.session_mode == "tty":
        directories.append(["/gnubox/.session_mode_tty", [0, 0, "0000"]])
    
        if current_project.enable_echo:
            directories.append(["/gnubox/.enable_echo", [0, 0, "0000"]])
    
        if current_project.enable_cursor:
            directories.append(["/gnubox/.enable_cursor", [0, 0, "0000"]])

    if current_project.boot_splash:
        directories.append(["/usr/share/plymouth/themes/bootlogo", [0, 0, "0755"]])
        directories.append(["/var/lib/plymouth", [0, 0, "0755"]])
        directories.append(["/var/spool/plymouth", [0, 0, "0755"]])
        directories.append(["/run/plymouth", [0, 0, "0755"]])
        items.append(["files/bootlogo", "/usr/share/plymouth/themes/bootlogo", [0, 0, "0644"]])

    if current_project.separate_data_partition:
        directories.append(["/data", [0, 0, "0755"]])

    setup_write_bins(builditems)
    items.append(["rootfs directory overlay", "/"])

    delete = []
    rebranding(delete, directories, items)

    builditems.append({
        "type": "directory",
        "name": "rootfs directory x2",
        "export": False,

        "directories": directories,
        "items": items
    })

    builditems.append({
        "type": "smart-chroot",
        "name": "rootfs directory",
        "export": current_project.export_rootfs_directory,

        "manual_validation": True,
        "use_systemd_container": True,
        "fix_systemd_container_host_files_copy": True,
        
        "source": "rootfs directory x2",
        "scripts": setup_chroot_script()
    })

    if current_project.export_rootfs_tar_gz:
        builditems.append({
            "type": "tar",
            "name": "rootfs.tar.gz",
            "export": True,

            "source": "rootfs directory",

            "gz": True
        })

    if current_project.export_rootfs_tar_xz:
        builditems.append({
            "type": "tar",
            "name": "rootfs.tar.xz",
            "export": True,

            "source": "rootfs directory",

            "xz": True
        })

    if current_project.export_rootfs_tar:
        builditems.append({
            "type": "tar",
            "name": "rootfs.tar",
            "export": True,

            "source": "rootfs directory"
        })

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

    cmdline = f"{"ro" if current_project.root_readonly else "rw"} rootwait=60 systemd.getty_auto=0 selinux=0 plymouth.ignore-serial-consoles mount_bootmnt {cmdline_console} preinit=/root/gnubox/system_preinit.sh {current_project.cmdline}"

    if current_project.boot_sound == "init":
        cmdline += " startupsound_afterModulesLoading=/startup.wav"
    
    if current_project.boot_sound == "logo" and current_project.boot_splash:
        cmdline += " startupsound_afterLogoShowOnlyAfterModules=/startup.wav"

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

    if True:
        cmdline += " logo.nologo"

    boot_splash_substring = " splash earlysplash"
    if current_project.boot_splash:
        cmdline += boot_splash_substring

    session_mode = current_project.session_mode
    if session_mode == "init":
        cmdline += " init=/gnubox/runshell.sh"

    if session_mode != "x11" and session_mode != "wayland" and current_project.screen_idle_time > 0:
        cmdline += f" consoleblank={current_project.screen_idle_time}"

    architectures = []
    builditems = []

    deleteAny(os.path.join(path_temp_syslbuild, "files"))
    deleteAny(os.path.join(path_temp_syslbuild, "chroot"))
    deleteAny(os.path.join(path_temp_syslbuild, "kernel_image"))
    deleteAny(os.path.join(path_temp_syslbuild, "blobs"))
    
    setup_build_architectures(builditems, architectures)
    setup_download(builditems)
    setup_build_base(builditems, cmdline)
    export.setup_build_targets(builditems, cmdline)

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

def updateProgress(value=0, text=None):
    if guiLoaded:
        if text is None:
            text = "Nothing"

        buildLog(f"{value} : {text}")
        
        gui_editor.progress["value"] = value
        gui_editor.progress_label["text"] = text
        gui_container.master.update_idletasks()
    else:
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

def update_project_structure():
    os.makedirs(path_resources, exist_ok=True)
    os.makedirs(path_temp, exist_ok=True)
    os.makedirs(path_temp_syslbuild, exist_ok=True)

    os.makedirs(os.path.join(path_resources, "chroot"), exist_ok=True)
    os.makedirs(os.path.join(path_resources, "files"), exist_ok=True)
    os.makedirs(os.path.join(path_resources, "initramfs"), exist_ok=True)

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

    create_empty_file("rpi_32_config_extension.txt")
    create_empty_file("rpi_64_config_extension.txt")

    gitignore_path = os.path.join(current_project_directory, ".gitignore")
    if not os.path.isfile(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("output\n")
            f.write(".temp\n")
            f.write("last.log\n")

    init_devicetree("opi_zero3")
    init_devicetree("rpi_64")
    init_devicetree("rpi_32")

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
            show_error(f"you have the syslbuild {version.formatVersion(version.VERSION)} version, while the project was saved in a newer version of {version.formatVersion(current_project.gnubox_version)}")
            return False
        elif version_diff < 0:
            current_project.gnubox_version = version.VERSION.copy()
            raw_save_project(path, current_project)
        else:
            current_project.gnubox_version = version.VERSION.copy()
    else:
        current_project = Project()
        current_project.gnubox_version = version.VERSION.copy()
        raw_save_project(path, current_project)

    current_project_directory = os.path.dirname(path)
    current_project_name = os.path.basename(current_project_directory)
    path_temp = os.path.join(current_project_directory, ".temp")
    path_resources = os.path.join(current_project_directory, "resources")
    path_temp_syslbuild = os.path.join(path_temp, "syslbuild")
    path_temp_syslbuild_file = os.path.join(path_temp_syslbuild, "project.json")

    update_project_structure()

    return True

# ----------------------------------------

def run_editor(path):
    if load_project(path):
        show_frame(frame_editor)

def show_frame(frame):
    frame.tkraise()

def console_build():
    global guiLoaded

    guiLoaded = False
    if len(sys.argv) > 1:
        if load_project(sys.argv[1]):
            build_project()
        sys.exit(0)

def gui_base():
    global gui_window
    global guiLoaded

    guiLoaded = True
    gui_window = tk.Tk()
    gui_window.title("Gnubox maker")
    gui_window.geometry("1200x700")

    gui_window.update_idletasks()
    width = gui_window.winfo_width()
    height = gui_window.winfo_height()
    x = (gui_window.winfo_screenwidth() // 2) - (width // 2)
    y = (gui_window.winfo_screenheight() // 2) - (height // 2)
    gui_window.geometry(f'{width}x{height}+{x}+{y}')

    gui_container = tk.Frame(gui_window)
    gui_container.pack(fill="both", expand=True)
    return gui_container

def main():
    global frame_editor
    global gui_container

    console_build()

    gui_container = gui_base()
    frame_openproject = gui_open_project.create_frame(gui_container, run_editor)
    frame_editor = gui_editor.create_frame(gui_container, build_project)

    show_frame(frame_openproject)
    gui_window.mainloop()

# ----------------------------------------

from internal_utils import *
from devicetree_funcs import *

import gui_open_project
import gui_editor

from initramfs import *

import rpi_export
import opi_zero3_export

import export

if __name__ == "__main__":
    main()