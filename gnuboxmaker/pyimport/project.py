from __main__ import *
import __main__

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

def build_project():
    updateProgress(10, "Generating the syslbuild project...")
    generate_syslbuild_project()

    updateProgress(50, "Launching syslbuild...")
    if run_syslbuild():
        updateProgress(100, "Completed")
        time.sleep(2)
        updateProgress()
    else:
        if __main__.guiLoaded:
            failed_to_build()
        else:
            stop_error("Failed to build")

def update_project_structure():
    import internal_utils
    import devicetree_funcs

    os.makedirs(__main__.path_resources, exist_ok=True)
    os.makedirs(__main__.path_temp, exist_ok=True)
    os.makedirs(__main__.path_temp_syslbuild, exist_ok=True)

    os.makedirs(os.path.join(__main__.path_resources, "chroot"), exist_ok=True)
    os.makedirs(os.path.join(__main__.path_resources, "files"), exist_ok=True)
    os.makedirs(os.path.join(__main__.path_resources, "initramfs"), exist_ok=True)

    runshell_path = os.path.join(__main__.path_resources, "runshell.sh")
    if not os.path.isfile(runshell_path):
        internal_utils.copyFile(runshell_path, "gnuboxmaker/runshell.sh")

    preinit_path = os.path.join(__main__.path_resources, "preinit.sh")
    if not os.path.isfile(preinit_path):
        internal_utils.copyFile(preinit_path, "gnuboxmaker/preinit.sh")

    logo_path_png = os.path.join(__main__.path_resources, "logo.png")
    logo_path_gif = os.path.join(__main__.path_resources, "logo.gif") # gif на экране загрузки еще не реализован
    if not os.path.isfile(logo_path_png) and not os.path.isfile(logo_path_gif):
        internal_utils.copyFile(logo_path_png, "gnuboxmaker.png")

    logo_updating_path_png = os.path.join(__main__.path_resources, "logo_updating.png")
    logo_updating_path_gif = os.path.join(__main__.path_resources, "logo_updating.gif")
    if not os.path.isfile(logo_updating_path_png) and not os.path.isfile(logo_updating_path_gif):
        internal_utils.copyFile(logo_updating_path_png, "gnuboxmaker/logo_updating.png")

    startup_sound = os.path.join(__main__.path_resources, "startup.wav")
    if not os.path.isfile(startup_sound):
        internal_utils.copyFile(startup_sound, "gnuboxmaker/startup.wav")

    internal_utils.create_empty_file("rpi_32_config_extension.txt")
    internal_utils.create_empty_file("rpi_64_config_extension.txt")

    gitignore_path = os.path.join(__main__.current_project_directory, ".gitignore")
    if not os.path.isfile(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("output\n")
            f.write(".temp\n")
            f.write("last.log\n")

    devicetree_funcs.init_devicetree("opi_zero3")
    devicetree_funcs.init_devicetree("rpi_64")
    devicetree_funcs.init_devicetree("rpi_32")

def load_project(path):
    import internal_utils

    if os.path.isfile(path):
        __main__.current_project = internal_utils.raw_load_project(path)
        version_diff = internal_utils.checkVersion(__main__.current_project)
        if version_diff > 0:
            show_error(f"you have the syslbuild {version.formatVersion(version.VERSION)} version, while the project was saved in a newer version of {version.formatVersion(__main__.current_project.gnubox_version)}")
            return False
        elif version_diff < 0:
            __main__.current_project.gnubox_version = version.VERSION.copy()
            internal_utils.raw_save_project(path, __main__.current_project)
        else:
            __main__.current_project.gnubox_version = version.VERSION.copy()
    else:
        __main__.current_project = Project()
        __main__.current_project.gnubox_version = version.VERSION.copy()
        internal_utils.raw_save_project(path, __main__.current_project)

    __main__.current_project_directory = os.path.dirname(path)
    __main__.current_project_name = os.path.basename(__main__.current_project_directory)
    __main__.path_temp = os.path.join(__main__.current_project_directory, ".temp")
    __main__.path_resources = os.path.join(__main__.current_project_directory, "resources")
    __main__.path_temp_syslbuild = os.path.join(__main__.path_temp, "syslbuild")
    __main__.path_temp_syslbuild_file = os.path.join(__main__.path_temp_syslbuild, "project.json")

    update_project_structure()

    return True
