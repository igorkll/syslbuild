# Gnubox maker (The GUI is not finished)
![preview](https://raw.githubusercontent.com/igorkll/Gnubox-Maker/refs/heads/main/preview.png)  
the easiest way is to create an embedded/kiosk linux distribution with a single application that cannot be exited  
it uses a patched linux kernel, which prevents switching VT and using ctrl+alt+del  
Gnubox maker works on the image generation principle. that is, first you create a Gnubox maker project on your computer, set all the necessary settings, add files and packages, and then assemble the project for the platforms you need and write the resulting firmware to the target devices  
the source code of gnubox maker is located in the syslbuild repository as it is part of a single project: https://github.com/igorkll/syslbuild  
Attention! since the gnubox maker projects are building from root in the host system, be careful what you build  
Gnubox Maker creates a special Linux system for a single application. After launching, you cannot exit it or switch to other programs. Everything you need to work is assembled automatically from files and scripts, and the system is immediately ready for use  
By default, Gnubox maker provides a completely clean loading screen (with your logo optional) and the complete inability to exit the application embedded in the image  
Gnubox maker is ideally suited for: household appliances, ATM, car radios, smart home control panels  
wherever you need a closed linux for one application, Gnubox maker will be an ideal option for generating an image for a ready-made device  
A minimum of 100 GB of free space on a PC is recommended for using Gnubox maker  
Gnubox maker secures the build from the project, which allows you to save the configuration and repeat the build of the system  
as well as Gnubox maker projects can be controlled via git  
The .img images for x86 / x86_64 that Gnubox maker generates are universal. they can be written to a USB drive or to a hard disk/SSD. also, when the device is turned on for the first time, the partition size will increase to the maximum possible (up to the entire available disk space) so that the OS can use all available space  
a similar program for creating Windows images for embedded devices: https://github.com/igorkll/WinBox-Maker  
ATTENTION. Starting from version 1.3.9, the kernels do not go with the program, but are assembled on the user's computer during installation. because of this, the installation can take a long time. up to several hours  
if your task requires an even simpler program, you can consider mkbootable: https://github.com/igorkll/mkbootable  
If you don't have enough gnubox maker features or you need a minimum image size, you can go down a level and use syslbuild directly: https://github.com/igorkll/syslbuild  

## subprojects
* syslbuild (main) - a low-level build system for custom linux distributions: https://github.com/igorkll/syslbuild
* Gnubox maker - the simplest way to create kiosk/appliance builds of gnu/linux: https://github.com/igorkll/Gnubox-Maker
* mkbootable - an even easier way to make a kiosk/single application gnu/linux: https://github.com/igorkll/mkbootable

## installing
* download the syslbuild release (NOT THE REPOSITORY BRANCH): https://github.com/igorkll/syslbuild/releases
* unpack it in a convenient place
* launch install.sh from root
* wait for the installation process to finish (it can take up to 4 hours)
* the unpacked files can now be deleted
### supported host systems
recommended OS: Ubuntu 24.04 LTS (Noble Numbat)  
tested on OS: linux mint
* debian
* ubuntu
* linux mint

## roadmap
* gui with system settings and choice of platforms for export
* add support for creating 64-bit images for 32-bit UEFI (yes, for those very old intel atom tablets)
* add support for custom kernels
* increase the display time of the logo so that the user does not have to look at a black screen

## bugs
* HDMI audio does not work on orange pi zero 3 (it works on raspberry pi 64)
* "screen idle time" does not work on wayland
* wifi is not working on orange pi zero 3
* gpu is not working on orange pi zero 3
* 32 bit arm and rpi_32 NOT SUPPORTED IN THE MOMENT

## supported platforms
* x86_64 (BIOS, UEFI)
* x86 (BIOS, UEFI)
* orange pi zero 3
* raspberry pi 5/4/3 (i tested this on raspberry pi 5, but in theory the image created via raspberry pi 64 should work on 5/4/3)
* 32 bit arm and rpi_32 NOT SUPPORTED IN THE MOMENT
if the platform you need is not available in gnubox maker, you can use syslbuild (a lower-level tool for creating embedded linux builds) where you can customize the build for any hardware you are interested in and do anything with the system  
alternatively, you can fork gnubox maker and then offer a pull request  

## projects used
* syslbuild: https://github.com/igorkll/syslbuild
* linux-embedded-patchs: https://github.com/igorkll/linux-embedded-patchs
* embedded-plymouth: https://github.com/igorkll/embedded-plymouth
* custom-debian-initramfs-init: https://github.com/igorkll/custom-debian-initramfs-init
* linux-embedded-setup-scripts: https://github.com/igorkll/linux-embedded-setup-scripts
* liamounts: https://github.com/igorkll/liamounts
* super-kiosk-browser: https://github.com/igorkll/super-kiosk-browser

## what was disabled
* ESC button in plymouth (plymouth source code patch)
* ctrl+alt+del in the linux kernel (kernel source patch)
* switching VT (kernel source patch + configs)
* sysrq (kernel source patch)
* tty signals & control flow (kernel source patch)
* keyboard echo at the very beginning of the boot (kernel source patch)
* keyboard echo in tty shell mode (just disabled by default)

## platforms support rate (from 0 to 10)
* x86 - 9/10
* raspberry pi 64 - 9/10
* orange pi zero 3 - 4/10

## used kernel patches (from https://github.com/igorkll/linux-embedded-patchs)
* disable_vt_swithing_from_keyboard.patch - prevents the possibility of switching VT from the keyboard
* disable_vt_swithing_from_wayland.patch - prevents the possibility of VT switching in wayland composers that do not have a setting that allows you to disable this (weston have setting to disable VT switching)
* disable_sysrq.patch - removes the sysrq mechanism from the kernel
* disable_cad.patch - eliminates the possibility of using ctrl+alt+del to reboot the device from the keyboard
* disable_keyboard_echo_by_default.patch - prevents typing characters on the screen from the keyboard before launching plymouth
* disable_tty_control_flow.patch - disables control flow in the kernel
* disable_tty_signals.patch - disables tty signals in the kernel
* disable_reboot_and_shutdown_emerg_messages.patch - disables the output of shutdown/reboot messages.
* make_all_emerg_messages_with_alert_loglevel.patch - makes all EMERG messages with loglevel alert so that they can be stopped using loglevel=0

## project structure
* gnubox.gnb - the main file
* resources - all project resources used during the build process
* resources/files - files that will be copied to rootfs before executing chroot scripts. please note that all your files and directories from this directory will have rights 755 and belong to root, regardless of what rights they have during the build. this is necessary for repeatable assembly on different machines. if you need to change the permissions on the target system, use the "chroot" scripts.
* resources/chroot - scripts executed inside a chroot in the system during the build process (not just a chroot, but a systemd-nspawn container) please note that at the end of each file you need to create an empty file or directory with the path "/.chrootend" otherwise the build will fail
* resources/initramfs - you can add additional files directly to initramfs
* resources/runshell.sh - the shell startup file. you can write a script directly in it if you use tty mode and you will just get console output, or you can run your application from it if you use wayland/x11
* resources/preinit.sh - this script runs before the initialization system in the initramfs environment. at this point, the switch_root has not yet occurred and the real root is mounted in "/root"
* resources/logo.png - the logo that will be used when bootloading with splash enabled
* resources/logo_updating.png - the logo that will be used when updating with splash enabled
* resources/startup.wav - the sound that will be used during the booting. requires configuration with a special parameter in the project. turned off by default
* resources/rpi_32_config_extension.txt - configuration extensions for RPI 32
* resources/rpi_64_config_extension.txt - configuration extensions for RPI 64
* output - the finished result of the build
* .temp - temporary files used during the build process

## devicetree
you can create a custom devicetree to connect the perepherals
* devicetree/PLATFORM_NAME/override.txt - you can specify overrides for .dtb/.dts here, specify a name without an extension
* devicetree/PLATFORM_NAME/overlays.txt - here you can specify a list of overlays .dtbo/.dtso specify names without extension by separating the names with a line break
* devicetree/PLATFORM_NAME - here you can add your .dtb and .dtbo files to the image. you can also add it here.dts and .dtso files and they will end up in the image as already compiled .dtb and .dtbo

## startup sound modes
* none - the power-on sound is not used
* init - It plays the sound as early as possible. almost immediately after loading the audio driver. ideal for devices without a screen like Bluetooth speakers.
* logo - It plays a sound when the load logo appears. It ONLY works with "boot_splash" enabled AND DOES NOT WORK on devices without a screen.

## how self-update works
The update itself allows you to update the device's firmware automatically using the same .img image that gnubox maker exports  
in order for the self-update function to be available to you, make sure that the "allow_updatescript" flag is set in the project configuration  
to start the self-update, you need to call the /self_update.sh script with root rights and pass him the path to the .img file  
if your shell runs as root, then this will not be a problem. if not, you can come up with your own way to increase privileges  
for example, you can use a daemon running from root that will monitor a special path for the presence of an update file  
alternatively, you can use a SUID binary that will accept the update file, validate it, and if everything is fine, then run a self-update (be careful with SUID)  
keep in mind that the script itself /self_update.sh It DOES NOT VALIDATE the incoming .img file at ALL  
he just assumes that the .img that you passed to /self_update.sh is the same .img that you recorded on the device and that it is suitable for this device  
please note that the bootloader will not be affected during the self-update  
also for launching /self_update.sh an .img file passed as a path to /self_update.sh must be located on the "DATA" section  
using the script /self_update.sh it is impossible without a separate DATA section enabled. this script will not be in rootfs at all in this case  
when self-updating, only the "BOOT" and "rootfs" sections are updated. also note that gnubox maker uses "BOOT" ONLY on single-board computers. on x86, there is an EFI partition (if the image is EFI-enabled), but it is not updated using self-update because it refers to the bootloader.  
please note that the partition sizes CANNOT be increased during the update. therefore, when building the first image, reserve enough space for future updates using "minsize_root_partition" and "minsize_boot_partition" or "size_boot_partition" and "size_root_partition"  

## args
* you can pass the path to the *.gnb file to gnubox maker and the build will happen automatically after which the program will terminate. The GUI will not appear

## WARNINGS
* at the end of each script, you must create an empty file or directory from the chroot folder at the end using the path "/.chrootend" to make sure that the script is executed correctly. if you don't do this, the build will fail
* "files" that will be copied to rootfs before executing chroot scripts. please note that all your files and directories from this directory will have rights 755 and belong to root, regardless of what rights they have during the build. this is necessary for repeatable assembly on different machines. if you need to change the permissions on the target system, use the "chroot" scripts.
* "chroot" is executed in systemd-nspawn
* Attention! since the gnubox maker projects are building from root in the host system, be careful what you build
* despite the presence of command-line arguments for building via tty, gnubox maker must BE run from its working directory (otherwise it will not work)
* in order for GPU acceleration to work on raspberry pi 64, you need to select at least this debian version: trixie 20260217T143331Z. older versions have a Mesa version that is incompatible with the raspberry pi board
* if you use boot splash, single-board computers will wait for framebuffer to appear when turned on and will not continue booting without a connected monitor.
* DO NOT USE "boot_splash" on devices without a screen. Since on some platforms the initialization script will wait for the framebuffer to appear so that the user sees the logo, as a result, the device will not start at all. You can use startup sound in init mode, for example, to inform the user that the device's power is on.
* during the build, a lot is downloaded from the Internet. The assembly will not work without a network connection
* in the system image built through gnubox maker, it is STRONGLY RECOMMENDED NOT to use the apt and dpkg package manager, much less update the system using them. There is a /self_update.sh mechanism for updating and to install applications on a ready-made embedded device, I recommend implementing flatpak

## notes
* please note that by default, the first time you turn on the created root image, the partition will be enlarged to the maximum possible size for the current media. this is done because I cannot know what size of drive the *.img image will be written to
* by default, the allow_updatescript feature from custom-debian-init-script is enabled. to understand how it works, read this: https://github.com/igorkll/custom-debian-initramfs-init
* if your script is runshell.sh when is completed, it will automatically restart. (not working in session mode "init")
* gnubox maker uses a hook on the shutdown/reboot/poweroff commands to use the --no-wall argument and the user does not see the shutdown message. however, if your shell does shutdown/reboot in a different way instead of launching shutdown/reboot/poweroff in the console, the user will still see the wall message, and you yourself must prevent this.
* the /var directory is mounted as tmpfs
* The .img images for x86 / x86_64 that Gnubox maker generates are universal. they can be written to a USB drive or to a hard disk/SSD.
* if session_mode init is set then runshell.sh in fact, it will be an init system, you do everything yourself. and it will always be run from root
* the real boot partition is mounted in the "/bootmnt" directory and is accessible from updatescript via the path "/updateroot/bootmnt"
* if you use a separate data partition for data, it will be expanded the first time you turn it on, regardless of root_expand. the root_expand itself will be IGNORED and the root partition will NOT be expanded
* the data partition is created with the ext4 filesystem in the /data directory
* to build gnubox maker from source after cloning the repository, run "prepair.sh ". this is necessary to build a default kernel.
* the "separate_data_partition_home_link" parameters make the /home and /root directories symlinks to their copies in the /data section. it only works with "separate_data_partition" enabled
* the "separate_data_partition_var_link" parameter makes the /var directory a symlink to its copy in /data. it only works with "separate_data_partition" enabled and automatically turns "var_is_temp" off

## what should I do if the project build fails?
* make sure that EACH of your chroot scripts creates a /.chrootend file at the end
* check the last.log in the root of the project and make sure everything is correct
* try to build it a few more times
* restart your computer and try again
* delete the directories .temp and output (clear the temporary project files) and try again
* try to build a project from the examples of gnubox maker, and if it is going to, then the problem is in your project. If not, it's possible that there are some dependencies missing or your host system is not supported
* try to build the project on a virtual machine with Ubuntu 24.04 LTS

## how do I rebuild kernels in the gnubox maker program?
* local kernel rebuild for the project is not supported yet.
* you need to change the source code of the program
* open the gnuboxmaker/kernel_build directory and build kernel_build.json via syslbuild
* delete all contents of gnuboxmaker/kernel_image and replace with gnuboxmaker/kernel_build/output
