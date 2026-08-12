from __main__ import *
import __main__

def any_rpi(builditems):
    builditems.append({
        "architectures": ["arm64", "armhf"],

        "type": "gitclone",
        "name": "rpi_firmware",
        "export": False,

        "git_url": "https://github.com/raspberrypi/firmware",
        "git_branch": "master",
        "git_checkout": "1.20250915"
    })

    if __main__.current_project.integrate_raspberry_firmwares_if_need:
        builditems.append({
            "architectures": ["arm64", "armhf"],

            "type": "gitclone",
            "name": "rpi_wireless_firmware",
            "export": False,

            "git_url": "https://github.com/RPi-Distro/firmware-nonfree",
            "git_branch": "trixie",
            "git_checkout": "9794282eb9f4a2de1f23b41a738926740e975d83"
        })

def any_rpi_rootfs_tweaks(rootfs_tbl):
    if __main__.current_project.session_mode == "x11":
        rootfs_tbl["items"].append(["files/fix-rpi-x11.conf", "/etc/X11/xorg.conf.d/fix-rpi-x11.conf", RIGHTS_644_755])

    return rootfs_tbl

def export_rpi_32(builditems, cmdline, appendPartitions):
    config_txt = read_gnubox_file("rpi_32_config.txt") + "\n" + read_project_file("resources/rpi_32_config_extension.txt")

    override = get_devicetree_override("rpi_32")
    if override:
        config_txt += f"\ndevice_tree={override}.dtb"

    overlays = get_devicetree_overlays("rpi_32")
    for overlay in overlays:
        config_txt += f"\ndtoverlay={overlay}"

    writeText(os.path.join(__main__.path_temp_syslbuild, "files", "cmdline_rpi_32.txt"), exclude_string("root=/dev/mmcblk0p2 " + cmdline + f" {getWaitFbStr(True)}\n", __main__.current_project.exclude_cmdline))
    writeText(os.path.join(__main__.path_temp_syslbuild, "files", "config_rpi_32.txt"), config_txt)

    items = [
        ["rootfs directory", "."],
        ["kernel_image/arm64/rpi_64/kernel_modules", "/usr", RIGHTS_644_755],
        ["kernel_image/armhf/rpi_kernel/kernel_modules", "/usr", RIGHTS_644_755],
        ["kernel_image/armhf/rpi_kernel7/kernel_modules", "/usr", RIGHTS_644_755]
    ]

    if __main__.current_project.integrate_raspberry_firmwares_if_need:
        items.append(["rpi_wireless_firmware/debian/config/brcm80211/brcm", "/lib/firmware/brcm", RIGHTS_644_755])
        items.append(["rpi_wireless_firmware/debian/config/brcm80211/cypress", "/lib/firmware/cypress", RIGHTS_644_755])

    builditems.append(any_rpi_rootfs_tweaks({
        "architectures": ["armhf"],

        "type": "directory",
        "name": "rootfs directory RPI 32",
        "export": False,

        "items": items
    }))

    setup_export_initramfs(builditems, "rpi_32")

    items = [
        ["rpi_firmware/boot/COPYING.linux", "/COPYING.linux"],
        ["rpi_firmware/boot/LICENCE.broadcom", "/LICENCE.broadcom"],
        ["rpi_firmware/boot/overlays", "/overlays"],
        ["rpi_firmware/boot/fixup.dat", "/fixup.dat"],
        ["rpi_firmware/boot/fixup4.dat", "/fixup4.dat"],
        ["rpi_firmware/boot/fixup4cd.dat", "/fixup4cd.dat"],
        ["rpi_firmware/boot/fixup4db.dat", "/fixup4db.dat"],
        ["rpi_firmware/boot/fixup4x.dat", "/fixup4x.dat"],
        ["rpi_firmware/boot/fixup_cd.dat", "/fixup_cd.dat"],
        ["rpi_firmware/boot/fixup_db.dat", "/fixup_db.dat"],
        ["rpi_firmware/boot/fixup_x.dat", "/fixup_x.dat"],
        ["rpi_firmware/boot/start.elf", "/start.elf"],
        ["rpi_firmware/boot/start4.elf", "/start4.elf"],
        ["rpi_firmware/boot/start4cd.elf", "/start4cd.elf"],
        ["rpi_firmware/boot/start4db.elf", "/start4db.elf"],
        ["rpi_firmware/boot/start4x.elf", "/start4x.elf"],
        ["rpi_firmware/boot/start_cd.elf", "/start_cd.elf"],
        ["rpi_firmware/boot/start_db.elf", "/start_db.elf"],
        ["rpi_firmware/boot/start_x.elf", "/start_x.elf"],
        ["rpi_firmware/boot/bootcode.bin", "/bootcode.bin"],

        ["kernel_image/arm64/rpi_5/boot", "/"], # тут некоторые dtb лежат. по этому добавляю все равно даже в 32 битный образ, хотя само ядро от RPI 5 тут не нужно

        ["kernel_image/arm64/rpi_64/boot", "/"],
        ["kernel_image/arm64/rpi_64/kernel.img", "/kernel8.img"],
        ["kernel_image/arm64/rpi_64/kernel_config", "/kernel8_config"],
        ["initramfs_rpi_64.img", "/initramfs8"],
        
        ["kernel_image/armhf/rpi_kernel/boot", "/"],
        ["kernel_image/armhf/rpi_kernel/kernel.img", "/kernel.img"],
        ["kernel_image/armhf/rpi_kernel/kernel_config", "/kernel_config"],
        ["initramfs_rpi_kernel.img", "/initramfs"],

        ["kernel_image/armhf/rpi_kernel7/boot", "/"],
        ["kernel_image/armhf/rpi_kernel7/kernel7.img", "/kernel7.img"],
        ["kernel_image/armhf/rpi_kernel7/kernel7_config", "/kernel7_config"],
        ["initramfs_rpi_kernel7.img", "/initramfs7"],

        ["files/cmdline_rpi_32.txt", "/cmdline.txt"],
        ["files/config_rpi_32.txt", "/config.txt"]
    ]

    dtbList = devicetree_get_files("rpi_32", "dtb")
    for dtb in dtbList:
        items.append([dtb, f"/{os.path.basename(dtb)}"])

    dtboList = devicetree_get_files("rpi_32", "dtbo")
    for dtbo in dtboList:
        items.append([dtbo, f"/overlays/{os.path.basename(dtbo)}"])

    builditems.append({
        "architectures": ["armhf"],

        "type": "directory",
        "name": "boot_rpi_32",
        "export": False,

        "items": items,

        "directories": [
            ["/rpi_32", [0, 0, "0000"]]
        ]
    })

    builditems.append({
        "architectures": ["armhf"],

        "type": "filesystem",
        "name": "boot_rpi_32.img",
        "export": False,

        "source": "boot_rpi_32",

        "fs_type": "fat32",
        "size": __main__.current_project.size_boot_partition,
        "minsize": __main__.current_project.minsize_boot_partition,
        "label": "BOOT"
    })

    builditems.append({
        "architectures": ["armhf"],

        "type": "filesystem",
        "name": "rootfs_rpi_32.img",
        "export": False,

        "source": "rootfs directory RPI 32",

        "fs_type": "ext4",
        "size": __main__.current_project.size_root_partition, 
        "minsize": __main__.current_project.minsize_root_partition,
        "label": "rootfs"
    })

    builditems.append({
        "architectures": ["armhf"],

        "type": "full-disk-image",
        "name": f"{__main__.current_project_name} RPI 32.img",
        "export": True,

        "size": "auto + (10 * 1024 * 1024)",

        "partitionTable": "dos",
        "partitions": [
            ["boot_rpi_32.img", "c"],
            ["rootfs_rpi_32.img", "linux"]
        ] + appendPartitions
    })

def export_rpi_64(builditems, cmdline, appendPartitions):
    config_txt = read_gnubox_file("rpi_64_config.txt") + "\n" + read_project_file("resources/rpi_64_config_extension.txt")

    override = get_devicetree_override("rpi_64")
    if override:
        config_txt += f"\ndevice_tree={override}.dtb"

    overlays = get_devicetree_overlays("rpi_64")
    for overlay in overlays:
        config_txt += f"\ndtoverlay={overlay}"

    writeText(os.path.join(__main__.path_temp_syslbuild, "files", "cmdline_rpi_64.txt"), exclude_string("root=/dev/mmcblk0p2 " + cmdline + f" {getWaitFbStr(True)}\n", __main__.current_project.exclude_cmdline))
    writeText(os.path.join(__main__.path_temp_syslbuild, "files", "config_rpi_64.txt"), config_txt)

    items = [
        ["rootfs directory", "."],
        ["kernel_image/arm64/rpi_64/kernel_modules", "/usr", RIGHTS_644_755],
        ["kernel_image/arm64/rpi_5/kernel_modules", "/usr", RIGHTS_644_755]
    ]

    if __main__.current_project.integrate_raspberry_firmwares_if_need:
        items.append(["rpi_wireless_firmware/debian/config/brcm80211/brcm", "/lib/firmware/brcm", RIGHTS_644_755])
        items.append(["rpi_wireless_firmware/debian/config/brcm80211/cypress", "/lib/firmware/cypress", RIGHTS_644_755])

    builditems.append(any_rpi_rootfs_tweaks({
        "architectures": ["arm64"],

        "type": "directory",
        "name": "rootfs directory RPI 64",
        "export": False,

        "items": items
    }))

    setup_export_initramfs(builditems, "rpi_64")

    items = [
        ["rpi_firmware/boot/COPYING.linux", "/COPYING.linux"],
        ["rpi_firmware/boot/LICENCE.broadcom", "/LICENCE.broadcom"],
        ["rpi_firmware/boot/overlays", "/overlays"],
        ["rpi_firmware/boot/fixup.dat", "/fixup.dat"],
        ["rpi_firmware/boot/fixup4.dat", "/fixup4.dat"],
        ["rpi_firmware/boot/fixup4cd.dat", "/fixup4cd.dat"],
        ["rpi_firmware/boot/fixup4db.dat", "/fixup4db.dat"],
        ["rpi_firmware/boot/fixup4x.dat", "/fixup4x.dat"],
        ["rpi_firmware/boot/fixup_cd.dat", "/fixup_cd.dat"],
        ["rpi_firmware/boot/fixup_db.dat", "/fixup_db.dat"],
        ["rpi_firmware/boot/fixup_x.dat", "/fixup_x.dat"],
        ["rpi_firmware/boot/start.elf", "/start.elf"],
        ["rpi_firmware/boot/start4.elf", "/start4.elf"],
        ["rpi_firmware/boot/start4cd.elf", "/start4cd.elf"],
        ["rpi_firmware/boot/start4db.elf", "/start4db.elf"],
        ["rpi_firmware/boot/start4x.elf", "/start4x.elf"],
        ["rpi_firmware/boot/start_cd.elf", "/start_cd.elf"],
        ["rpi_firmware/boot/start_db.elf", "/start_db.elf"],
        ["rpi_firmware/boot/start_x.elf", "/start_x.elf"],
        ["rpi_firmware/boot/bootcode.bin", "/bootcode.bin"],

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
        "size": __main__.current_project.size_boot_partition,
        "minsize": __main__.current_project.minsize_boot_partition,
        "label": "BOOT"
    })

    builditems.append({
        "architectures": ["arm64"],

        "type": "filesystem",
        "name": "rootfs_rpi_64.img",
        "export": False,

        "source": "rootfs directory RPI 64",

        "fs_type": "ext4",
        "size": __main__.current_project.size_root_partition, 
        "minsize": __main__.current_project.minsize_root_partition,
        "label": "rootfs"
    })

    builditems.append({
        "architectures": ["arm64"],

        "type": "full-disk-image",
        "name": f"{__main__.current_project_name} RPI 64.img",
        "export": True,

        "size": "auto + (10 * 1024 * 1024)",

        "partitionTable": "dos",
        "partitions": [
            ["boot_rpi_64.img", "c"],
            ["rootfs_rpi_64.img", "linux"]
        ] + appendPartitions
    })
