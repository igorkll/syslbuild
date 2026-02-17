# Gnubox maker (BETA)
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
A minimum of 60 GB of free space on a PC is recommended for using Gnubox maker  
Gnubox maker secures the build from the project, which allows you to save the configuration and repeat the build of the system  
as well as Gnubox maker projects can be controlled via git  
The .img images for x86 / x86_64 that Gnubox maker generates are universal. they can be written to a USB drive or to a hard disk/SSD. also, when the device is turned on for the first time, the partition size will increase to the maximum possible (up to the entire available disk space) so that the OS can use all available space  
a similar program for creating Windows images for embedded devices: https://github.com/igorkll/WinBox-Maker  

## installing
* download the syslbuild release (NOT THE REPOSITORY BRANCH): https://github.com/igorkll/syslbuild/releases
* unpack it in a convenient place
* launch install.sh from root
* the unpacked files can now be deleted

## roadmap
* gui with system settings and choice of platforms for export
* x11 support (currently only wayland is supported)

## supported platforms
* x86_64 (BIOS, UEFI)
* x86 (BIOS, UEFI)
* orange pi zero 3
* raspberry pi 5/4/3 (i tested this on raspberry pi 5, but in theory the image created via raspberry pi 64 should work on 5/4/3)

## supported host systems
* debian
* ubuntu
* linux mint

## projects used
* syslbuild: https://github.com/igorkll/syslbuild
* linux-embedded-patchs: https://github.com/igorkll/linux-embedded-patchs
* embedded-plymouth: https://github.com/igorkll/embedded-plymouth
* custom-debian-initramfs-init: https://github.com/igorkll/custom-debian-initramfs-init

## what was disabled
* ESC button in plymouth (plymouth source code patch)
* ctrl+alt+del in the linux kernel (kernel source patch)
* switching VT (kernel source patch + configs)
* sysrq (kernel source patch)
* control flow & kerboard echo (it's just turned off by default in tty mode. you can enable)

## used kernel patches (from https://github.com/igorkll/linux-embedded-patchs)
* disable_vt_swithing_from_keyboard.patch - prevents the possibility of switching VT from the keyboard
* disable_vt_swithing_from_wayland.patch - prevents the possibility of VT switching in wayland composers that do not have a setting that allows you to disable this (weston have setting to disable VT switching)
* disable_sysrq.patch - removes the sysrq mechanism from the kernel
* disable_cad.patch - eliminates the possibility of using ctrl+alt+del to reboot the device from the keyboard
* disable_keyboard_echo_by_default.patch - prevents typing characters on the screen from the keyboard before launching plymouth

## project structure
* gnubox.gnb - the main file
* resources - all project resources used during the build process
* resources/files - files that will be copied to rootfs before executing chroot scripts. please note that all your files and directories from this directory will have rights 755 and belong to root, regardless of what rights they have during the build. this is necessary for repeatable assembly on different machines. if you need to change the permissions on the target system, use the "chroot" scripts.
* resources/chroot - scripts executed inside a chroot in the system during the build process (not just a chroot, but a systemd-nspawn container) please note that at the end of each file you need to create an empty file or directory with the path "/.chrootend" otherwise the build will fail
* resources/runshell.sh - the shell startup file. you can write a script directly in it if you use tty mode and you will just get console output, or you can run your application from it if you use wayland/x11
* resources/preinit.sh - this script runs before the initialization system in the initramfs environment. at this point, the switch_root has not yet occurred and the real root is mounted in "/root"
* resources/logo.png - the logo that will be used when uploading with splash enabled
* output - the finished result of the build
* .temp - temporary files used during the build process

## args
* you can pass the path to the *.gnb file to gnubox maker and the build will happen automatically after which the program will terminate. The GUI will not appear

## WARNINGS
* at the end of each script, you must create an empty file or directory from the chroot folder at the end using the path "/.chrootend" to make sure that the script is executed correctly. if you don't do this, the build will fail
* "files" that will be copied to rootfs before executing chroot scripts. please note that all your files and directories from this directory will have rights 755 and belong to root, regardless of what rights they have during the build. this is necessary for repeatable assembly on different machines. if you need to change the permissions on the target system, use the "chroot" scripts.
* "chroot" is executed in systemd-nspawn
* Attention! since the gnubox maker projects are building from root in the host system, be careful what you build
* despite the presence of command-line arguments for building via tty, gnubox maker must BE run from its working directory (otherwise it will not work)

## notes
* please note that by default, the first time you turn on the created root image, the partition will be enlarged to the maximum possible size for the current media. this is done because I cannot know what size of drive the *.img image will be written to
* by default, the allow_updatescript feature from custom-debian-init-script is enabled. to understand how it works, read this: https://github.com/igorkll/custom-debian-initramfs-init
* if your script is runshell.sh when is completed, it will automatically restart. (not working in session mode "init")
* It is always necessary to reboot and turn off the device from the you shell via "shutdown --no-wall now" and "shutdown --no-wall -r now", the --no-wall argument is REQUIRED so that the shutdown process is not visible when turned off.
* the /var directory is mounted as tmpfs
* The .img images for x86 / x86_64 that Gnubox maker generates are universal. they can be written to a USB drive or to a hard disk/SSD.
* if session_mode init is set then runshell.sh in fact, it will be an init system, you do everything yourself. and it will always be run from root

## what should I do if the project build fails?
* make sure that EACH of your chroot scripts creates a /.chrootend file at the end
* check the last.log in the root of the project and make sure everything is correct
* try to build it a few more times
* restart your computer and try again
* delete the directories .temp and output (clear the temporary project files) and try again
* try to build a project from the examples of gnubox maker, and if it is going to, then the problem is in your project. If not, it's possible that there are some dependencies missing or your host system is not supported

## how do I rebuild kernels in the gnubox maker program?
* local kernel rebuild for the project is not supported yet.
* you need to change the source code of the program
* open the gnuboxmaker/kernel_build directory and build kernel_build.json via syslbuild
* delete all contents of gnuboxmaker/kernel_image and replace with gnuboxmaker/kernel_build/output
