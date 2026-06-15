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

syslbuild_install_path = "/opt/syslbuild"
if os.path.isdir(syslbuild_install_path):
    syslbuild_path = syslbuild_install_path
else:
    syslbuild_path = "."

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

argsparser.add_argument("-o", "--output", default="image.img", help="output path to the boot image")

argsparser.add_argument("--boot-logo", default=None, help="you can set a custom boot logo .png")
argsparser.add_argument("--root-privileges", type=str2bool, default=False, help="if set to true, the application in the image will have root privileges")

args = argsparser.parse_args()

# --------------------------------------- get application info

def get_application_logo():
    return None

def get_application_session_type():
    suffix = pathlib.Path(args.application).suffix

    if suffix == ".sh":
        return "tty"
    
    return "wayland"

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
        "uartlogs": True,
        "uartlogs_speed": 115200,
        "uartlogs_rootshell": False,
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
        "session_mode": get_application_session_type(),
        "minlogotime": 10,
        "cmdline": "",
        "exclude_cmdline": [],
        "integrate_liamounts": False,
        "integrate_xwayland": True
    }

    project_config.update(platforms[args.platform]["project_config"])

    return project_config

def get_project_path(project_config):
    project_checksum = dict_checksum(project_config)
    project_path = os.path.join(os.path.expanduser("~"), ".mkbootable", project_checksum)
    os.makedirs(project_path, exist_ok=True)
    return project_path

def get_boot_logo():
    if args.boot_logo:
        return args.boot_logo

    application_logo = get_application_logo()
    if application_logo:
        return application_logo

    return os.path.join(syslbuild_path, "mkbootable.png")

def generate_project():
    project_config = generate_project_config()
    project_path = get_project_path(project_config)

    project_config_path = os.path.join(project_path, "gnubox.gnb")
    project_resources = os.path.join(project_path, "resources")

    if os.path.isdir(project_resources):
        shutil.rmtree(project_resources)
    os.makedirs(project_resources, exist_ok=True)

    with open(project_config_path, "w") as f:
        json.dump(project_config, f, indent=2, ensure_ascii=False)

    shutil.copy(get_boot_logo(), os.path.join(project_resources, "logo.png"))

    return project_path

def build_project(project_path):
    build_log(f"launch gnubox maker: {project_path}")

    project_config_path = os.path.join(project_path, "gnubox.gnb")

    cmd = [
        "bash", "-c",
        f"cd {syslbuild_path!r} && {sys.executable!r} {os.path.abspath('gnuboxmaker.py')!r} "
        f"{project_config_path!r}"
    ]
    
    subprocess.run(cmd)

# экспортирует новую версию образа
# перемешает файл, если раздел куда происходит экспорт является системным разделом то фактического копирования не будет
# если после следующей сборки файла нет. значит сработал кеш и перезаписывать его и не нужно
# но если экспорт происходит уже по новому пути то файл фактически не будет экспортирован до инвалидирования/очистки кеша
def export_image(project_path):
    image_path = platforms[args.platform]["image_path"]
    image_path = image_path.replace("@", os.path.basename(project_path))
    image_full_path = os.path.join(project_path, image_path)

    if os.path.isfile(image_full_path):
        shutil.move(image_full_path, args.output)
        build_log(f"image exported: {args.output}")
    else:
        build_log(f"the image has not been exported (cached)")

# ---------------------------------------

project_path = generate_project()
build_project(project_path)
export_image(project_path)
