from __main__ import *
import __main__

def setup_export_debian_initramfs(builditems, forPlatform):
    if forPlatform == "opi_zero3":
        builditems.append({
            "architectures": ["arm64"],

            "type": "debian-export-initramfs",
            "name": "initramfs_opi_zero3.img",
            "export": False,

            "kernel_config": "kernel_image/arm64/sunxi/kernel_config",
            "source": "rootfs directory OPI ZERO 3"
        })
    elif forPlatform == "rpi_64":
        builditems.append({
            "architectures": ["arm64"],

            "type": "debian-export-initramfs",
            "name": "initramfs_rpi_64.img",
            "export": False,

            "kernel_version": "6.12.47-embedded-rpi-64+",
            "kernel_config": "kernel_image/arm64/rpi_64/kernel_config",
            "source": "rootfs directory RPI 64"
        })

        builditems.append({
            "architectures": ["arm64"],

            "type": "debian-export-initramfs",
            "name": "initramfs_rpi_5.img",
            "export": False,

            "kernel_version": "6.12.47-embedded-rpi-5+",
            "kernel_config": "kernel_image/arm64/rpi_5/kernel_config",
            "source": "rootfs directory RPI 64"
        })
    elif forPlatform == "rpi_32":
        builditems.append({
            "architectures": ["armhf"],

            "type": "debian-export-initramfs",
            "name": "initramfs_rpi_kernel.img",
            "export": False,

            "kernel_version": "6.12.47-embedded-rpi-kernel+",
            "kernel_config": "kernel_image/arm/rpi_kernel/kernel_config",
            "source": "rootfs directory RPI 32"
        })

        builditems.append({
            "architectures": ["armhf"],

            "type": "debian-export-initramfs",
            "name": "initramfs_rpi_kernel7.img",
            "export": False,

            "kernel_version": "6.12.47-embedded-rpi-kernel7+",
            "kernel_config": "kernel_image/arm/rpi_kernel7/kernel_config",
            "source": "rootfs directory RPI 32"
        })
    else:
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

def setup_export_initramfs(builditems, forPlatform=None):
    if __main__.current_project.distro == "debian":
        setup_export_debian_initramfs(builditems, forPlatform)
    else:
        stop_error(f"unknown distro \"{__main__.current_project.distro}\"")
