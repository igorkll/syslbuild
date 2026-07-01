# mkbootable (BETA)
![preview](https://raw.githubusercontent.com/igorkll/mkbootable/refs/heads/main/preview.png)  
create a bootable linux image from your application  
there will be nothing superfluous in the boot image created from your application. no system hotkeys. no visual artifacts during loading like the flashing VT. just your logo followed immediately by the app  
the source code of mkbootable is located in the syslbuild repository as it is part of a single project: https://github.com/igorkll/syslbuild  
this project is an abstraction layer above Gnubox maker, which in turn is an abstraction layer above syslbuild  
all of this is part of a single syslbuild project  
the program cache is located at the path: /home/$USER/.mkbootable and can take up a HUGE AMOUNT  

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
* debian
* ubuntu
* linux mint

## supported platforms
there may be nuances in the support of some platforms. read about it here: https://github.com/igorkll/Gnubox-Maker  
* desktop_64 (default)
* desktop_32
* raspberry_pi_64
* orange_pi_zero3

## supported application types
* flatpak - the flatpak format package (NOT IMPLEMENTED AT THE MOMENT)
* AppImage - the AppImage application type
* binary - just a linux executable file
* sh - just a shell script. it will be launched in a text tty, but without control flow and other kernel terminal hotkeys
* html - the html file that will be opened in the browser

## application arguments
you have to pass one of them. but not more than one  
* --application - the path to your application's executable file
* --web - the link to the web page to be displayed in kiosk mode

## args
* --platform - select an available platform from the list (default: desktop_64)
* --mode - auto/graphic/console select one of the launch modes for your application. By default, the mode is automatically defined as graphical for binary files and text for shell scripts. but it's better to specify it explicitly.
* --boot-logo - you can set a custom boot logo .png
* --chroot - you can specify a chroot script to modify the system during the image build stage.
* --wifi-name - the name of the wifi network for automatic connection (NOT IMPLEMENTED AT THE MOMENT)
* --wifi-password - the password of the wifi network for automatic connection (NOT IMPLEMENTED AT THE MOMENT)
* --output - output path to the boot image
* --syslbuild - the path to the syslbuild directory. it will be detected automatically if your syslbuild is installed using the standard path in /opt/syslbuild

## flags
* --root-privileges - the application in the image will have root privileges
* --sudo-privileges - it is a more "soft" version of "root-privileges". the application will not be launched from root. but it will be able to get root by executing sudo. no password is required and the user will see sudo execution on the screen
* --multi-file - then not only the application file will be added to the image, but also all files from its directory. use carefully so as not to add unnecessary files to the image
* --debug - enable the kernel log and root shell at UART0 115200
* --clear-cache - cleans up the cache before building

## used projects
* super-kiosk-browser: https://github.com/igorkll/super-kiosk-browser - the browser used in the web kiosk mode
* syslbuild: https://github.com/igorkll/syslbuild - the program for building the images
* linux-embedded-patchs: https://github.com/igorkll/linux-embedded-patchs - a set of patches for using the linux kernel on embedded locked-down devices
* custom-debian-initramfs-init: https://github.com/igorkll/custom-debian-initramfs-init - custom /init script for debian initramfs
* embedded-plymouth: https://github.com/igorkll/embedded-plymouth - plymouth with a patch to disable ESC key processing (so that the console cannot be displayed during boot)

## screenshots
![preview](https://raw.githubusercontent.com/igorkll/syslbuild/refs/heads/main/screenshots/mkbootable/1.png)  
![preview](https://raw.githubusercontent.com/igorkll/syslbuild/refs/heads/main/screenshots/mkbootable/2.png)  
![preview](https://raw.githubusercontent.com/igorkll/syslbuild/refs/heads/main/screenshots/mkbootable/3.png)  
![preview](https://raw.githubusercontent.com/igorkll/syslbuild/refs/heads/main/screenshots/mkbootable/4.png)  
![preview](https://raw.githubusercontent.com/igorkll/syslbuild/refs/heads/main/screenshots/mkbootable/5.png)  
