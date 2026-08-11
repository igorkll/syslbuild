from __main__ import *

def export_opi_zero3(builditems, cmdline, appendPartitions):
    dtboList_active = []
    for overlay in get_devicetree_overlays("opi_zero3"):
        dtboList_active.append(overlay + ".dtbo")

    devicetree = get_devicetree_override("opi_zero3")
    if devicetree:
        devicetree = devicetree + ".dtb"
    else:
        devicetree = "sun50i-h618-orangepi-zero3.dtb"

    items = [
        ["rootfs directory x4", "."],

        ["sprdwl_ng", "/etc/modules-load.d/sprdwl_ng.conf", [0, 0, "0644"], True],

        ["kernel_image/arm64/sunxi/kernel_modules", "/usr", RIGHTS_644_755]
    ]

    if current_project.integrate_armbian_firmwares_if_need:
        items.append(["armbian_firmware", "/usr/lib/firmware", RIGHTS_644_755])

    if current_project.platform_opi_zero3_hdmi_audio_high_priority:
        conf = "&" + os.path.join(gnuboxmaker_dir, "opi_zero3_hdmi_audio_high_priority.conf")
        items.append([conf, "/etc/wireplumber/wireplumber.conf.d/hdmi-audio-priority.conf", [0, 0, "0644"]])

    builditems.append({
        "architectures": ["arm64"],

        "type": "directory",
        "name": "rootfs directory opi_zero3",
        "export": False,

        "items": items
    })

    builditems.append({
        "architectures": ["arm64"],

        "type": "filesystem",
        "name": "rootfs_opi_zero3.img",
        "export": False,

        "source": "rootfs directory opi_zero3",

        "fs_type": "ext4",
        "size": current_project.size_root_partition, 
        "minsize": current_project.minsize_root_partition,
        "label": "rootfs"
    })

    builditems.append({
        "architectures": ["arm64"],

        "type": "debian-export-initramfs",
        "name": "initramfs_opi_zero3.img",
        "export": False,

        "kernel_config": "kernel_image/arm64/sunxi/kernel_config",
        "source": "rootfs directory opi_zero3"
    })

    builditems.append({
        "architectures": ["arm64"],

        "type": "singleboard",
        "name": f"{current_project_name} OPI ZERO 3.img",
        "export": True,

        "singleboardType": "uboot-offset",

        "extlinux_path": "start.conf",
        "uboot_script": "&" + os.path.join(gnuboxmaker_dir, "uboot_bootscript.cmd"),

        "bootloader": "blobs/u-boot-sunxi-with-spl.bin",
        "bootloader_offset": 16,
        "bootloaderDtb": devicetree,

        "dtbList": devicetree_get_files("opi_zero3", "dtb"),
        "dtboList": devicetree_get_files("opi_zero3", "dtbo"),
        "dtboList_active": dtboList_active,

        "boot_part_items": [
            ["kernel_image/arm64/sunxi/dtbs", "/dtbs"]
        ],

        "trigger_boot_flag": "opi_zero3",

        "kernel": "kernel_image/arm64/sunxi/kernel.img",
        "initramfs": "initramfs_opi_zero3.img",
        "rootfs": "rootfs_opi_zero3.img",
        "appendPartitions": appendPartitions,

        "boot_partition_size": current_project.size_boot_partition,
        "boot_partition_minsize": current_project.minsize_boot_partition,
        "boot_partition_name": "BOOT",

        "kernel_args_auto": True,
        "kernel_rootfs_auto": "manual",
        "kernel_args": exclude_string(cmdline + f" cma={current_project.platform_opi_zero3_cma} {getWaitFbStr(False)}", current_project.exclude_cmdline) # why is "waitFbBeforeModules" here? because in this FUCKING Chinese board, half of the peripherals start with a fucking delay, and it should be initialized by the time plymouth is launched
    })
