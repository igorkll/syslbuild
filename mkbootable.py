#!/usr/bin/env python3
import argparse
import json
import sys
import os
import math
import hashlib
import shutil
import subprocess
import pathlib

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected")

def build_log(logstr, quiet=False):
    if not quiet:
        logstr = f"------------------------ MKBOOTABLE: {logstr}"
    
    print(logstr)

def dict_checksum(tbl):
    return hashlib.md5(json.dumps(tbl).encode('utf-8')).hexdigest()

# --------------------------------------- parsing cli arguments

argsparser = argparse.ArgumentParser(
    prog="mkbootable",
    description="create a bootable linux image from your application"
)

argsparser.add_argument("application", help="the path to your application's executable file")

argsparser.add_argument(
    "--platform",
    choices=["desktop_64", "desktop_32", "raspberry_pi_64", "orange_pi_zero3"],
    default="desktop_64",
    help="Target platform (default: desktop_64)"
)

argsparser.add_argument(
    "--mode",
    choices=["auto", "graphic", "console"],
    default="auto",
    help="the launch mode of your application (default: auto)"
)

argsparser.add_argument("--boot-logo", default=None, help="you can set a custom boot logo .png")
argsparser.add_argument("--root-privileges", type=str2bool, default=False, help="if set to true, the application in the image will have root privileges")
argsparser.add_argument("--multi-file", type=str2bool, default=False, help="if set to true, then not only the application file will be added to the image, but also all files from its directory. use carefully so as not to add unnecessary files to the image")
argsparser.add_argument("--debug", type=str2bool, default=False, help="if set to true, in UART0, the kernel log and root shell are running at 115200")
argsparser.add_argument("--clear-cache", type=str2bool, default=False, help="cleans up the cache before building")

argsparser.add_argument("-o", "--output", default="image.img", help="output path to the boot image")

args = argsparser.parse_args()

# --------------------------------------- get application info

def is_shebang(filepath):
    try:
        with open(filepath, 'rb') as f:
            header = f.read(2)
            return header == b'#!'
    except (IOError, OSError):
        return False

def get_application_path():
    if os.path.isfile(args.application):
        return args.application
    
    return shutil.which(args.application)

def get_application_session_type():
    if args.mode == "graphic":
        return "wayland"
    elif args.mode == "console":
        return "tty"

    suffix = pathlib.Path(application_path).suffix

    if suffix == ".sh" or is_shebang(application_path):
        return "tty"
    
    return "wayland"

def get_application_logo():
    return None

def get_application_run_features():
    suffix = pathlib.Path(application_path).suffix

    return {
        "packages": [],
        "command": f"cd /application && /application/{application_name}"
    }

# --------------------------------------- show info

syslbuild_install_path = "/opt/syslbuild"
if os.path.isdir(syslbuild_install_path):
    syslbuild_path = syslbuild_install_path
else:
    syslbuild_path = "."

application_path = get_application_path()
application_dir = os.path.dirname(application_path)
application_name = os.path.basename(application_path)
application_session_type = get_application_session_type()
application_logo = get_application_logo()
application_run_features = get_application_run_features()

build_log(f"syslbuild path: {syslbuild_path}")
build_log(f"application path: {application_path}")
build_log(f"application dir: {application_dir}")
build_log(f"application name: {application_name}")
build_log(f"application session type: {application_session_type}")
build_log(f"application logo: {application_logo}")
build_log(f"application run features: {application_run_features}")

# --------------------------------------- build project

platforms = {
    "desktop_64": {
        "project_config": {
            "export_x86_64": True,
            "export_x86": False,
            "export_arm64": False,
            "export_img_bios_mbr": False,
            "export_img_bios_gpt": False,
            "export_img_uefi_gpt": False,
            "export_img_bios_and_uefi_gpt": True,
            "export_img_opi_zero3": False,
            "export_img_rpi_64": False
        },
        "image_path": "output/amd64/@ BIOS UEFI GPT.img"
    },
    "desktop_32": {
        "project_config": {
            "export_x86_64": False,
            "export_x86": True,
            "export_arm64": False,
            "export_img_bios_mbr": False,
            "export_img_bios_gpt": True,
            "export_img_uefi_gpt": False,
            "export_img_bios_and_uefi_gpt": False,
            "export_img_opi_zero3": False,
            "export_img_rpi_64": False
        },
        "image_path": "output/i386/@ BIOS GPT.img"
    },
    "raspberry_pi_64": {
        "project_config": {
            "export_x86_64": False,
            "export_x86": False,
            "export_arm64": True,
            "export_img_bios_mbr": False,
            "export_img_bios_gpt": False,
            "export_img_uefi_gpt": False,
            "export_img_bios_and_uefi_gpt": False,
            "export_img_opi_zero3": False,
            "export_img_rpi_64": True
        },
        "image_path": "output/arm64/@ RPI 64.img"
    },
    "orange_pi_zero3": {
        "project_config": {
            "export_x86_64": False,
            "export_x86": False,
            "export_arm64": True,
            "export_img_bios_mbr": False,
            "export_img_bios_gpt": False,
            "export_img_uefi_gpt": False,
            "export_img_bios_and_uefi_gpt": False,
            "export_img_opi_zero3": True,
            "export_img_rpi_64": False
        },
        "image_path": "output/arm64/@ OPI ZERO 3.img"
    }
}

def generate_project_config():
    user_packages = [
        # audio
        "pipewire",
        "pipewire-pulse",
        "wireplumber",
        "libspa-0.2-modules",
        "alsa-utils",

        # libs
        "libpulse0",
        "libnspr4",
        "libnss3",
        "libxss1",
        "libasound2",
        "libatk1.0-0",
        "libatk-bridge2.0-0",
        "libxcomposite1",
        "libxcursor1",
        "libxdamage1",
        "libxrandr2",
        "libxkbcommon0",
        "libwayland-client0",
        "libwayland-egl1",
        "libgbm1",
        "libgtk-3-0",

        # tools
        "nano",

        # network
        "network-manager",
        "rfkill",
        "iproute2",
        "wpasupplicant",
        "wget",

        # other
        "udisks2" # i use the standard udisks2 instead of liamounts. since user applications may have no idea what liamounts is and how it differs from udisks2.
    ]

    user_packages += application_run_features["packages"]

    project_config = {
        "gnubox_version": [1, 4, 3],
        "distro": "debian",
        "user_packages": user_packages,
        "exclude_packages": [],
        "debian_variant": "minbase",
        "debian_suite": "trixie",
        "debian_snapshot": "http://snapshot.debian.org/archive/debian/20260217T143331Z",
        "screen_idle_time": 0,
        "HandlePowerKey": "poweroff",
        "HandleRebootKey": "reboot",
        "HandleSuspendKey": "ignore",
        "HandleHibernateKey": "ignore",
        "HandleLidSwitch": "ignore",
        "boot_quiet": False,
        "boot_splash": True,
        "boot_sound": "none",
        "dont_show_splash_on_poweroff": True,
        "dont_use_splash_on_efi": False,
        "uartlogs": args.debug,
        "uartlogs_speed": 115200,
        "uartlogs_rootshell": args.debug,
        "exclude_tty1_from_consoles": True,
        "exclude_tty1_from_consoles_in_quiet": True,
        "make_tty1_primary_console": False,
        "splash_bg": "0, 0, 0",
        "splash_updating_bg": "0, 0, 0",
        "splash_mode": "contain",
        "splash_scale": 0.5,
        "use_separate_splash_for_update": False,
        "root_expand": False,
        "root_readonly": False,
        "allow_updatescript": True,
        "separate_data_partition": True,
        "separate_data_partition_home_link": True,
        "separate_data_partition_var_link": True,
        "separate_data_partition_etc_link": True,
        "var_is_temp": False,
        "minsize_boot_partition": "64MB",
        "minsize_efi_partition": "64MB",
        "minsize_root_partition": "64MB",
        "minsize_data_partition": "64MB",
        "size_boot_partition": "(auto * 1.2) + (100 * 1024 * 1024)",
        "size_efi_partition": "256MB",
        "size_root_partition": "(auto * 1.2) + (100 * 1024 * 1024)",
        "weston_shell": "kiosk",
        "session_user": "root" if args.root_privileges else "user",
        "session_mode": application_session_type,
        "minlogotime": 10,
        "cmdline": "clear noCursorBlink vt.global_cursor_default=0",
        "exclude_cmdline": [],
        "integrate_liamounts": False,
        "integrate_xwayland": True
    }

    project_config.update(platforms[args.platform]["project_config"])

    return project_config

def get_project_checksum(project_config):
    return dict_checksum(project_config)

def get_project_path(project_config):
    # project_checksum = get_project_checksum(project_config)
    project_path = os.path.join(os.path.expanduser("~"), ".mkbootable", "project")
    os.makedirs(project_path, exist_ok=True)
    return project_path

def get_boot_logo():
    if args.boot_logo:
        return args.boot_logo

    if application_logo:
        return application_logo

    return os.path.join(syslbuild_path, "mkbootable.png")

def generate_project():
    # ------------------------------------------ application base structure

    build_log("make application structure...")

    project_config = generate_project_config()
    project_path = get_project_path(project_config)

    project_config_path = os.path.join(project_path, "gnubox.gnb")
    project_resources = os.path.join(project_path, "resources")
    project_temp = os.path.join(project_path, ".temp")
    project_output = os.path.join(project_path, "output")

    if args.clear_cache:
        shutil.rmtree(project_temp)
        shutil.rmtree(project_output)

    if os.path.isdir(project_resources):
        shutil.rmtree(project_resources)
    os.makedirs(project_resources, exist_ok=True)

    # ------------------------------------------ write base files

    build_log("writing base files...")

    with open(project_config_path, "w") as f:
        json.dump(project_config, f, indent=2, ensure_ascii=False)

    shutil.copy(get_boot_logo(), os.path.join(project_resources, "logo.png"))

    project_files = os.path.join(project_resources, "files")
    os.makedirs(project_files)

    # ------------------------------------------ copy application files and make application command

    build_log("copying application files...")

    target_dir = os.path.join(project_files, "application")
    os.makedirs(target_dir)

    if args.multi_file:
        shutil.copytree(
            application_dir,
            target_dir,
            dirs_exist_ok=True
        )
    else:
        shutil.copy(application_path, os.path.join(target_dir, application_name))

    application_command = application_run_features["command"]

    # ------------------------------------------ write runshell.sh

    build_log("writing runshell.sh...")

    project_runshell = os.path.join(project_resources, "runshell.sh")
    with open(project_runshell, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(application_command)

    return project_path

def build_project(project_path):
    build_log(f"launch gnubox maker: {project_path}")

    project_config_path = os.path.join(project_path, "gnubox.gnb")

    cmd = [
        "bash", "-c",
        f"cd {syslbuild_path!r} && {sys.executable!r} {os.path.join(syslbuild_path, 'gnuboxmaker.py')!r} "
        f"{project_config_path!r}"
    ]
    
    subprocess.run(cmd)

def export_image(project_path):
    image_path = platforms[args.platform]["image_path"]
    image_path = image_path.replace("@", os.path.basename(project_path))
    image_full_path = os.path.join(project_path, image_path)

    build_log("copy image file...")
    shutil.copy(image_full_path, args.output)
    build_log(f"image exported: {args.output}")

# ---------------------------------------

project_path = generate_project()
build_project(project_path)
export_image(project_path)
