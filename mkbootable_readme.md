# mkbootable
![preview](https://raw.githubusercontent.com/igorkll/mkbootable/refs/heads/main/preview.png)  
create a bootable linux image from your application  
there will be nothing superfluous in the boot image created from your application. no system hotkeys. no visual artifacts during loading like the flashing VT. just your logo followed immediately by the app  
the source code of mkbootable is located in the syslbuild repository as it is part of a single project: https://github.com/igorkll/syslbuild  
this project is an abstraction layer above Gnubox maker, which in turn is an abstraction layer above syslbuild  
all of this is part of a single syslbuild project  

## subprojects
* syslbuild - a low-level build system for custom linux distributions: https://github.com/igorkll/syslbuild
* Gnubox maker - the simplest way to create kiosk/appliance builds of gnu/linux: https://github.com/igorkll/Gnubox-Maker
* mkbootable - an even easier way to make a kiosk/single application gnu/linux: https://github.com/igorkll/mkbootable

## installing
* download the syslbuild release (NOT THE REPOSITORY BRANCH): https://github.com/igorkll/syslbuild/releases
* unpack it in a convenient place
* launch install.sh from root
* the unpacked files can now be deleted

## supported platforms
* desktop_64 (default)
* desktop_32
* raspberry_pi_64
* orange_pi_zero3

## supported application types
* flatpak - the flatpak format package
* AppImage - the AppImage application type
* binary - just a linux executable file
* sh - just a shell script. it will be launched in a text tty, but without control flow and other kernel terminal hotkeys
* html - the html file that will be opened in the browser

