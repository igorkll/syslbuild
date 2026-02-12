# Gnubox maker
![preview](https://raw.githubusercontent.com/igorkll/syslbuild/refs/heads/main/gnuboxmaker_preview.png)  
the easiest way is to create an embedded/kiosk linux distribution with a single application that cannot be exited  
it uses a patched linux kernel, which prevents switching VT and using ctrl+alt+del  
the source code of gnubox maker is located in the syslbuild repository as it is part of a single project: https://github.com/igorkll/syslbuild

## projects used
* syslbuild: https://github.com/igorkll/syslbuild
* linux-embedded-patchs: https://github.com/igorkll/linux-embedded-patchs
* embedded-plymouth: https://github.com/igorkll/embedded-plymouth
* custom-debian-initramfs-init: https://github.com/igorkll/custom-debian-initramfs-init

## what was disabled
* ESC button in plymouth (source code patch)
* ctrl+alt+del in the linux kernel (source code patch)
* switching VT (source code patch + configs)

## project structure
* gnubox.gnb - the main file
* resources - all project resources used during the build process
* resources/files - files that will be copied to rootfs before executing chroot scripts. please note that all your files and directories from this directory will have rights 755 and belong to root, regardless of what rights they have during the build. this is necessary for repeatable assembly on different machines. if you need to change the permissions on the target system, use the "chroot" scripts.
* resources/chroot - scripts executed inside a chroot in the system during the build process (not just a chroot, but a systemd-nspawn container) please note that at the end of each file you need to create an empty file or directory with the path "/.chrootend" otherwise the build will fail
* output - the finished result of the build
* .temp - temporary files used during the build process

## WARNINGS
* at the end of each script, you must create an empty file or directory from the chroot folder at the end using the path "/.chrootend" to make sure that the script is executed correctly. if you don't do this, the build will fail
* "files" that will be copied to rootfs before executing chroot scripts. please note that all your files and directories from this directory will have rights 755 and belong to root, regardless of what rights they have during the build. this is necessary for repeatable assembly on different machines. if you need to change the permissions on the target system, use the "chroot" scripts.
* "chroot" is executed in systemd-nspawn

## notes
* please note that by omission, the first time you turn on the created root image, the partition will be enlarged to the maximum possible size for the current media. this is done because I cannot know what size of drive the *.img image will be written to
