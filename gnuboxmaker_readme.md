# Gnubox maker
![preview](https://raw.githubusercontent.com/igorkll/syslbuild/refs/heads/main/gnuboxmaker_preview.png)  
the easiest way is to create an embedded/kiosk linux distribution with a single application that cannot be exited  
it uses a patched linux kernel, which prevents switching VT and using ctrl+alt+del  

## what was disabled
* ESC button in plymouth (source code patch)
* ctrl+alt+del in the linux kernel (source code patch)
* switching VT (source code patch + configs)

## project structure
* gnubox.gnb - the main file
* resources - all project resources used during the build process
* resources/chroot - scripts executed inside a chroot in the system during the build process (not just a chroot, but a systemd-nspawn container) please note that at the end of each file you need to create an empty file or directory with the path "/.chrootend" otherwise the build will fail
* output - the finished result of the build
* .temp - temporary files used during the build process

## WARNINGS
* at the end of each script, you must create an empty file or directory from the chroot folder at the end using the path "/.chrootend" to make sure that the script is executed correctly. if you don't do this, the build will fail