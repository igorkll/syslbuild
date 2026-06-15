#!/usr/bin/env python3
import argparse

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected")

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

argsparser.add_argument("--boot-logo", default=None, help="you can set a custom boot logo")
argsparser.add_argument("--root-privileges", type=str2bool, default=False, help="if set to true, the application in the image will have root privileges")

args = argsparser.parse_args()

# ---------------------------------------

project_configs

def generate_gnuboxmaker_config():
    project_config = {
        "gnubox_version": [1, 4, 3],
        "distro": "debian",
        "user_packages": [
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
        ],
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
        "session_user": "root",
        "session_mode": "wayland",
        "minlogotime": 10,
        "cmdline": "",
        "exclude_cmdline": [],
        "integrate_liamounts": False,
        "integrate_xwayland": True
    }

    project_config
