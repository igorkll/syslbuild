from __main__ import *
import __main__

def export_x86(builditems):
    setup_export_initramfs(builditems)

    builditems.append({
        "architectures": ["amd64", "i386"],

        "type": "directory",
        "name": "rootfs directory x86",
        "export": False,

        "items": [
            ["rootfs directory", "."],
            ["initramfs.img", "/initramfs.img", [0, 0, "0644"]]
        ]
    })

    builditems.append({
        "architectures": ["amd64", "i386"],

        "type": "filesystem",
        "name": "rootfs.img",
        "export": False,

        "source": "rootfs directory x86",

        "fs_type": "ext4",
        "size": __main__.current_project.size_root_partition, 
        "minsize": __main__.current_project.minsize_root_partition,
        "label": "rootfs"
    })

def setup_build_targets(builditems, cmdline):
    if __main__.current_project.export_img_bios_mbr or __main__.current_project.export_img_bios_gpt or __main__.current_project.export_img_uefi_gpt or __main__.current_project.export_img_bios_and_uefi_gpt:
        export_x86(builditems)

    appendPartitions = []

    grub_info = {
        "type": "grub",
        "config": "grub.cfg",
        "modules": [
            "normal",
            "part_msdos",
            "part_gpt",
            "ext2",
            "configfile"
        ],
        "build": "linux-bootloaders/grub/build/no-welcome-2.14"
    }

    if __main__.current_project.separate_data_partition:
        builditems.append({
            "type": "filesystem",
            "name": "data.img",
            "export": False,

            "fs_type": "ext4",
            "size": __main__.current_project.minsize_data_partition,
            "label": "DATA",

            "chmod": [
                ["/", "1777", False]
            ],

            "chown": [
                ["/", 0, 0, False]
            ]
        })
        appendPartitions.append(["data.img", "linux"])

    if __main__.current_project.export_img_bios_mbr:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{__main__.current_project_name} BIOS MBR.img",
            "export": True,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "dos",
            "partitions": [
                ["rootfs.img", "linux"]
            ] + appendPartitions,

            "bootloader": grub_info | {
                "boot": 0
            }
        })

    if __main__.current_project.export_img_bios_gpt or __main__.current_project.export_img_bios_and_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "filesystem",
            "name": "bios boot.img",
            "export": False,

            "size": "1M"
        })

    if __main__.current_project.export_img_bios_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{__main__.current_project_name} BIOS GPT.img",
            "export": True,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["bios boot.img", "bios"],
                ["rootfs.img", "linux"]
            ] + appendPartitions,

            "bootloader": grub_info | {
                "boot": 1
            }
        })

    if __main__.current_project.export_img_uefi_gpt or __main__.current_project.export_img_bios_and_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "filesystem",
            "name": "uefi boot.img",
            "export": False,

            "fs_arg": "-F32",
            "fs_type": "fat",
            "size": __main__.current_project.size_efi_partition,
            "label": "EFI",

            "minsize": __main__.current_project.minsize_efi_partition
        })

    if __main__.current_project.export_img_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{__main__.current_project_name} UEFI GPT.img",
            "export": True,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["uefi boot.img", "efi"],
                ["rootfs.img", "linux"]
            ] + appendPartitions,

            "bootloader": grub_info | {
                "esp": 0,
                "boot": 1
            }
        })

    if __main__.current_project.export_img_bios_and_uefi_gpt:
        builditems.append({
            "architectures": ["amd64", "i386"],

            "type": "full-disk-image",
            "name": f"{__main__.current_project_name} BIOS UEFI GPT.img",
            "export": True,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["uefi boot.img", "efi"],
                ["bios boot.img", "bios"],
                ["rootfs.img", "linux"]
            ] + appendPartitions,

            "bootloader": grub_info | {
                "esp": 0,
                "boot": 2,
                "efiAndBios": True
            }
        })

    if __main__.current_project.export_img_opi_zero3:
        opi_zero3_export.export_opi_zero3(builditems, cmdline, appendPartitions)

    if __main__.current_project.export_img_rpi_32 or __main__.current_project.export_img_rpi_64:
        rpi_export.any_rpi(builditems)

    if __main__.current_project.export_img_rpi_32:
        rpi_export.export_rpi_32(builditems, cmdline, appendPartitions)

    if __main__.current_project.export_img_rpi_64:
        rpi_export.export_rpi_64(builditems, cmdline, appendPartitions)
