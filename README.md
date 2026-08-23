# syslbuild + gnubox maker + mkbootable 1.8.5
an build system for creating Linux distributions. it is focused on embedded distributions  
DOWNLOAD THE RELEASE, NOT THE REPOSITORY!  
WARNING!!! if you read this text from GITHUB page please, download a release and read description there. on github this text is DEV syslbuild version (not released yet)  
![preview](https://raw.githubusercontent.com/igorkll/syslbuild/refs/heads/main/preview.png)  
* the program requires root access because it mounts images
* WARNING! syslbuild runs from root during the build process, and the project can run code on the host system at the time of build.
* for this reason, treat syslbuild projects as executable files with full access. since they can execute code from root on the host system at the time of build
* if you don't want to run this on the host system to avoid providing root access, you can run this in a container / VM
* syslbuild allows you to automate the distribution build process, which is suitable for small custom distributions
* syslbuild is focused on building distributions for embedded systems (kiosks, navigators, and DVRs)
* in syslbuild, the build process is described by writing json with individual build elements (filesystems, kernels, bootloaders)
* syslbuild is able to create a boot image with a partition table itself, which can be convenient for creating a complete firmware.
* please note that in syslbuild, the runtime environment may affect the build result. a better solution would be to create one VM for the entire project and build the project on that VM. it is better that the architecture matches the target architecture of the assembly, although this is not necessary due to qemu-static

## subprojects
* syslbuild (main) - a low-level build system for custom linux distributions: https://github.com/igorkll/syslbuild
* Gnubox maker - the simplest way to create kiosk/appliance builds of gnu/linux: https://github.com/igorkll/Gnubox-Maker
* mkbootable - an even easier way to make a kiosk/single application gnu/linux: https://github.com/igorkll/mkbootable

## installing
* download the syslbuild release (NOT THE REPOSITORY BRANCH): https://github.com/igorkll/syslbuild/releases
* unpack it in a convenient place
* launch install.sh from root
* wait for the installation process to finish (it can take up to 2 hours)
* the unpacked files can now be deleted
### supported host systems
recommended OS: Ubuntu 24.04 LTS (Noble Numbat)  
* debian
* ubuntu
* linux mint

## the programs included in the package
* syslbuild - creating custom linux systems from an assembly description file. allows you to fully control and customize the system. export to any platforms is possible
* gnubox maker - a higher-level utility designed for creating kiosks and single application linux. wherever linux with a single application is needed (although this is not the only scenario), it supports export to a limited number of platforms
* mkbootable - A VERY high-level utility. you need it if you literally already have a ready-made application and you just need to make a bootable image from your application. He can't do anything else

## what should I choose syslbuild, Gnubox maker or mkbootable?
syslbuild is a low-level utility where you describe the system build yourself and can thoroughly control all partitions and files  
gnubox maker is a high-level GUI program for creating kiosks and application linux systems. the main use case is single application linux  
* if you need to thoroughly control the system you are building and be able to fully customize it - syslbuild
* if you just need a way to create kiosk/application linux that runs one of your applications - gnubox maker
* if you need custom hardware that is not available in the export support of gnubox maker - syslbuild
* I just need a bootable image right now - mkbootable

## dependency chain within the project
* syslbuild - main program
* gnubox maker - it works via syslbuild
* mkbootable - it works via gnubox maker

## the level of customization of the system in different programs of the package
* syslbuild - complete customization of the assembled system
* gnubox maker - partial customization. but most of them are already set up to create a kiosk
* mkbootable - almost zero customization. Just download the app and get a bootable image

## you may also be interested in
* https://github.com/igorkll/linux-embedded-patchs - a set of patches for using the linux kernel on embedded locked-down devices
* https://github.com/igorkll/custom-debian-initramfs-init - custom /init script for debian initramfs
* https://github.com/igorkll/WinBox-Maker - a program for creating embedded Windows images
* https://github.com/igorkll/embedded-plymouth - plymouth with a patch to disable ESC key processing (so that the console cannot be displayed during boot)

## build process
you create a folder and in it a json file with a description of the project  
it describes the build items, each of which can be 'exported' and/or used in another build items  
if you set the 'export' flag to true in the build item, the build item will appear in the output directory after the build, otherwise it will remain in .temp but can be used for other build items during the build process  
for example, for a phone whose bootloader usually loads the kernel from the raw partition, you can separately assemble the rootfs and the kernel separately and export them separately  
for a computer, you can build a kernel, but not export it, but assemble the debian base system separately. after create a file system, copy debian and the kernel into it, and then add another build item that will make an img with a bootloader and MBR  
the build in syslbuild is heavily divided into items, for example, you can't just assemble a module into a file system. First, you need to create a separate item directory and then add it to the file system  
also, assembling a bootable img with an already installed system is also a separate build item in which you must add file systems, etc  

## warnings
* remember that if the result of building your OS is .img with an already installed system (via "full-disk-image" for PCs or "singleboard" for boards like orangepi), then your initramfs should expand the data partition or rootfs to the maximum when the device is turned on for the first time. this is necessary because otherwise the user will not be able to use all the available media space
* I would also recommend that you change the UUID and PART-UUID of the rootfs partition when you turn on the device for the first time in order to avoid root substitution in the future if you use UUID/PART-UUID to mount rootfs.
* and you must change the UUID from PART-UUID and partition expansion in a script executed from initramfs while rootfs is not yet mounted.
* in the paths in the target directory of the builditem "directory" in the "items" and "directories" fields, do not create multiple directories in one call. since even though the path will be set automatically, when automatically creating directories, access rights to them are automatically set as 0700. the same thing in "items", if one or more directories from the path did not exist, they will be created, but they will be created with access rights 0700, which can cause very difficult bugs to debug. the use of chains is allowed only for file systems that do not support access rights, or if access rights do not matter in your assembled system (for example, the application runs from root, although there may be problems in this case) or the file system will be mounted via bindfs

## arguments
* -h - show help info
* --arch ARCHITECTURE - set the output architecture of the build
* -n - does the build anew, does not use the cache (syslbuild caches the kernel source code anyway, even in this mode. use -d if you want to download the kernel again)
* -d - do not use the download cache of the kernel sources
* -e - completely clears the entire cache before building
* --enable-chroot - enable the build inside the chroot container (WORK IN PROCESS)

## supported export architectures
* ALL - builds a project for all architectures from the list of project architectures
* amd64
* i386
* arm64
* armhf
* armel

## dependencies
* python3 / pip
* mmdebstrap - to build debian based systems
* pacman/pacstrap - to build arch linux based systems
* mkfs.* - you need support for the file systems that you intend to use in your projects
* qemu (qemu-user-static binfmt-support) - needed for debian cross-build
* wget
* cp
* dd
* truncate
* mount
* umount
* chmod
* chown
* sudo - either run syslbuild from root yourself, or you should have sudo and it will do it itself
* sfdisk
* grub-install
* x86_64-linux-gnu-gcc - different gcc builds for different architectures
* i686-linux-gnu-gcc
* aarch64-linux-gnu-gcc
* arm-linux-gnueabihf-gcc
* arm-linux-gnueabi-gcc
* grub-mkrescue/xorriso - to build iso images
* tar
* make
* gzip / zcat
* git
* mkimage (u-boot-tools)
* systemd-container
* reset
* device-tree-compiler
* bash
* 7z
* patch
* rsync
* cpio
* initramfs-tools
* diffutils
* binutils-arm-linux-gnueabi / binutils-aarch64-linux-gnu

## python dependencies
* json5
* asteval
* favicon
* requests
* Pillow

## installing dependencies on debian systems
```
sudo apt install -y \
  python3 wget sudo git make tar gzip \
  coreutils util-linux mount \
  ncurses-bin systemd-container
sudo apt install -y \
  e2fsprogs dosfstools btrfs-progs xfsprogs
sudo apt install -y \
  mmdebstrap qemu-user-static binfmt-support
sudo apt install -y \
  grub-pc-bin grub-efi-amd64-bin grub-common \
  xorriso
sudo apt install -y \
  gcc-x86-64-linux-gnu \
  gcc-i686-linux-gnu \
  gcc-aarch64-linux-gnu \
  gcc-arm-linux-gnueabihf \
  gcc-arm-linux-gnueabi
sudo apt install -y u-boot-tools
sudo apt install -y arch-install-scripts
sudo apt install -y grub-efi-ia32-bin grub-common
sudo apt install -y device-tree-compiler
sudo apt install -y 7zip 7zip-rar
sudo apt install -y patch
sudo apt install -y bc bison flex libssl-dev libelf-dev
sudo apt install -y rsync cpio initramfs-tools diffutils
sudo apt install -y pip
sudo apt install -y fdisk
sudo apt install -y binutils-arm-linux-gnueabi binutils-aarch64-linux-gnu

sudo pip install json5 --break-system-packages
sudo pip install asteval --break-system-packages
sudo pip install favicon --break-system-packages
sudo pip install requests --break-system-packages
sudo pip install Pillow --break-system-packages
```

## docs
* mmdebstrap: https://manpages.debian.org/testing/mmdebstrap/mmdebstrap.1.en.html

## build items types
* debian - debian build via mmdebstrap
* arch-linux - arch linux build via pacstrap
* arch-package - download arch linux package via pacman (It's not working right now)
* download - downloads the file
* directory - allows you to assemble many items into one (for example, to pack them into a file system later) allows you to set file owners and their rights
* filesystem - builds a file system from the specified items and sets the specified access rights for the files
* tar - collects archive from directory in tar format
* full-disk-image - creates a bootable image of a raw img disk that can be written to the root of the disk via dd or some etcher and it will immediately become bootable (the ability to boot depends on the settings)
* from-directory - extracts a file/directory from a directory
* gcc-build - builds something through GCC
* kernel - builds the core. you can provide a link to the kernel source code, patches for it, and the kernel config
* grub-iso-image - collects the bootable iso
* initramfs - collects initramfs from a directory
* unpack-initramfs - unpacking initramfs
* debian-update-initramfs - allows you to update initramfs (for debian systems) for the specified rootfs. this is necessary if you are building your kernel and you need to install its modules in rootfs first and only then update initramfs. the specified rootfs must also contain the kernel configuration for which the ramdisk is being updated. exports new rootfs with initramfs, not initramfs itself. your rootfs must have the "initramfs-tools" package and the kernel modules installed.
* debian-export-initramfs - it works the same way as debian-update-initramfs, but accepts the kernel config separately (not required if the config is already in your rootfs) and exports initramfs itself, not the entire rootfs with it. your rootfs must have the "initramfs-tools" package and the kernel modules installed.
* smart-chroot - executes scripts inside the chroot. if the processor architecture does not match, then this builditem itself will copy and then delete qemu-static from your chroot. exports a new rootfs with executed chroot scripts inside
* include - it allows you to connect another json file from the project, which in turn should contain only an array of builditems and nothing more at its root. In this case, the builditems array must be at the very root and immediately contain the builditem dictionaries.
* singleboard - a specially created builditem for creating images for single-board computers like the orange pi. its use is optional. you can completely replicate the "singleboard" builditem by combining other builditems to get a more complex behavior.
* gitclone - clones the repository from git. it allows you to specify a branch and checkout
* execute-commands - if there is no "source", it simply executes commands from the project directory. if there is a "source", it clones it and executes commands in it.
* unpack-archive - unpacks the archive. use 7z
* unpack-tar-gz - unpacks the tar.gz archive. use tar util
* unpack-tar-auto - unpacks the tar.* archive. use tar util
* build-configure-make - builds something from source if configure and make are used for the build.
* build-make - builds something from source if make are used for the build.
* patches - It allows you to patch your source files

## build items features
* debian supports the "_min" variant, which is essentially a "custom" but with a minimal set package required for assembly

## the order of assembly
### this is just the order that you should use to properly understand the syslbuild concept
* ready-made distributions/module assembly/packages download - starting point (builditems: debian, download)
* combining all modules, packages, and distributions into one directory (or several if you want to create multiple partitions in the future) (builditem: directory)
* packing a directory into a file system (builditem: filesystem, tar)
* pack the disk image (builditem: full-disk-image)

## supported bootloaders
* grub
* binary - just insert the binary bootloader to the specified address in the full-disk-image. required for signleboard

## aliases of names for partitions IDs (GPT / MBR)
* linux - 0FC63DAF-8483-4772-8E79-3D69D8477DE4 / 83
* swap - 0657FD6D-A4AB-43C4-84E5-0933C84B4F4F / 82
* efi - C12A7328-F81F-11D2-BA4B-00A0C93EC93B / ef
* bios - 21686148-6449-6E6F-744E-656564454649 / None

## debian kernel types
* default
* realtime

## builditem universal keys
* architectures - if the builditem contains this array, the builditem will only be built for the architectures listed in it.
* forkbase - marks this builditem as a base element for forks.
* fork - creates a fork from the nearest previous builditem marked with `forkbase`. when dictionaries are merged, matching keys overwrite each other. arrays also overwrite each other unless `forkArraysCombine` is enabled.
* forkArraysCombine - works only in the builditem that performs the fork (not in `forkbase`). if set to true, arrays are merged instead of overwritten during fork creation. default value is `false`.
* template - excludes the builditem from the build process. intended for use with `forkbase`. if set to `true`, the builditem itself will not be built, but it can still be used as a base for forks. this key is not inherited during forking.
* deleteBuildItemKeys - removes keys from the resulting builditem. intended for use with `fork`. can be placed inside any object within the builditem.
* build-if-filter-exists - if set to `true`, the builditem will only be built when at least one filter is specified.
* build-if-filter-not-exists - if set to `true`, the builditem will only be built when no filters are specified.
* build-if-all-filters-exists - array of filter names. the builditem will only be built if all specified filters are present.
* build-if-one-filter-exists - array of filter names. the builditem will only be built if at least one specified filter is present.
* build-if-not-all-filters-exists - array of filter names. the builditem will not be built if all specified filters are present.
* build-if-not-one-filter-exists - array of filter names. the builditem will not be built if at least one specified filter is present.
* build-if-no-filters-or-one-filter-exists - build an element if no filters are set or at least one matches
* input - if your builditem exports a directory, and the previous builditem also exports a directory, you can specify "input" to use the previous builditem as the basis for the new one. it is convenient to use when building libraries that depend on each other by combining with @previous and sysroot
* marker - if set to true, it updates the last "marker" element

## virtual builditems (start with @)
you cannot name your builditems starting with the @ symbol, as this refers to the virtual builditems described here  
* @previous - previous builditem
* @marker - the last item of the build marked with a marker (the marker field is set to true)

## keys that are not inherited by fork
* forkbase - these are the control keys of the fork itself, they are not inherited by the fork
* fork
* forkArraysCombine
* template - this key is used to exclude any builditem from the build. created for use with forkbase

## default kernel config changes
these changes to the kernel config are applied automatically when building the kernel in syslbuild unless the "kernel_config_disable_default_changes" parameter is set to true
* CONFIG_WERROR=n - this is necessary for the functionality of some of my patches
* CONFIG_RD_GZIP=y

## debug
* full disk image | x86_64 | BIOS: qemu-system-x86_64 \
  -enable-kvm -cpu host \
  -m 2048 -smp 4 \
  -drive file=output/amd64/disk.img,format=raw
* full disk image | x86_64 | UEFI: qemu-system-x86_64 \
  -enable-kvm -cpu host \
  -m 2048 -smp 4 \
  -drive file=output/amd64/disk.img,format=raw \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd
* iso image | x86 | BIOS: qemu-system-i386 -enable-kvm -cpu host -cdrom output/i386/lifeimage.iso -boot d -m 2048
* with sound: qemu-system-x86_64 -enable-kvm -cpu host -m 2048 -smp 4 -drive file=output/i386/mp3play.img,format=raw   -audiodev pa,id=snd0   -device intel-hda   -device hda-duplex,audiodev=snd0
* with sound and serial: qemu-system-x86_64 -enable-kvm -cpu host -m 2048 -smp 4 -drive file=output/i386/mp3play.img,format=raw   -audiodev pa,id=snd0   -device intel-hda   -device hda-duplex,audiodev=snd0 -serial stdio
* debug singleboard: picocom -b 115200 /dev/ttyUSB0

## roadmap
* add the ability to add additional files to the iso images
* support for the operation (packing and unpacking) of initramfs with a multiblock structure
* add riscV support and an example for the opencomputers 2 mod in minecraft
* an assembly element that collects popular ready-made modules into your rootfs. such as glibc, coreutils, busybox and other gnu utilities
* the ability to use the specified version of grub to create images, rather than the one provided in the host system
* built-in chroot environment for running syslbuild and other package programs
### completed
* execution of arbitrary scripts in the system's chroot, with qemu-static support for execution during assembly for a different architecture
* make a normal caching system
* the ability to add custom files when building the kernel. sometimes it is necessary, for example, for boards with wifi to download the regulatory.db or, for example, to build the ubuntu kernel, where you need a couple of .pem files
* exporting the resulting kernel config when building the kernel
* the ability to specify changes for kernel config parameters directly in the builditem of the kernel build
* support "architectures" and "template" for "include" builditem
* account for "binaries" files in caching in the "full-disk-image" builditem
* the ability to include additional files with builditems
* built-in export support for popular single-boarders and pine phone and librem 5. I want to make a builditem that downloads the bootloader for the specified single-board itself and builds the image using the transferred kernel, rootfs, initramfs and settings
* to save the source code of more than one kernel for one architecture (so that the cache works normally when building multiple cores for one architecture)
* in directory items, you can specify the rights for directories and files in copy objects separately.
* the ability to specify a filesystem revision

## singleboards whose assembly is guaranteed to work
* orange pi zero 3
* raspberry pi 64 bit - through the "full-disk-image" manually. export via "singleboard" to this platform is not supported

## project example
```json
{
    "min-syslbuild-version": [0, 2, 0],

    // you can announce this list and build a system for all architectures at once
    // just specify --arch ALL when starting syslbuild
    //"architectures": [
    //    "amd64",
    //    "arm64"
    //],

    "builditems": [
        {
            "type": "include",
            "file": "project_part.json"
        },

        // ---------------- raw commands execute
        // executes commands from the project's root directory
        // please do not use it in this form to modify existing builditems.
        // as this will lead to cache failures and cross-compilation issues. instead,
        // attach it to the builditem that you need to change via the "source" attribute and it will export the new builditem.
        {
            "type": "execute-commands",
            "name": "any unique name", //despite the fact that if you don't bind execute-commands to anything, it won't export anything. Each builditem must still have a unique name.

            "commands": [
                "any shell command",
                "any shell command 2"
            ],
        },

        // executes commands in the assembly element specified in the "source" parameter. exports the result
        {
            "type": "execute-commands",
            "name": "output name", //the name to export
            "export": false,

            // the name of the builditem that you want to modify using the command, and which will act as the root directory
            "source": "my builditem",

            // commands for modifying "my builditem"
            "commands": [
                "any shell command", 
                "any shell command 2"
            ],
        },

        // use custom pwd
        {
            "type": "execute-commands",
            "name": "any unique name",

            "working_dir": "any path",

            "commands": [
                "any shell command",
                "any shell command 2"
            ],
        },


        // ----------------

        {
            "type": "unpack-archive",
            "name": "unpacked",

            "archive": "/path/to/archive.zip"
        },
        {
            "type": "unpack-tar-gz",
            "name": "unpacked",

            // optional
            "strip_components": 0,

            "archive": "/path/to/archive.tar.gz"
        },
        {
            "type": "unpack-tar-auto",
            "name": "unpacked",

            // optional
            "strip_components": 0,

            "archive": "/path/to/archive.tar.xz"
        },

        // ---------------- building custom executable
        {
            "type": "gcc-build",
            "name": "custom-executable",
            "export": false,

            // optional. allows you to use the directory as a sysroot for gcc
            "sysroot": "any builditem directory",

            "CFLAGS": [
                "-O2",
                "-ffreestanding",
                "-Wall",
                "-Wextra"
            ],
            "LDFLAGS": [
                "-static"
            ],

            // specify a list of executable files OR directories for executable files
            //"sources": []
            "sources-dirs": ["my-sources"],
            "sources-dirs-extensions": [".c", ".cpp"], //optional. if this is not specified, syslbuild will take all files.
            "sources-dirs-recursive": true,
            "sources-dirs-exclude": ["my-sources/src/luac.c"], //optional
            
            "forkbase": true //marking the builditem as the base for creating forks
        },
        // you can create forks, and even multiple forks from a single forkbase. This can be used, for example, for cross-assembly, to set up the assembly of some complex element once and then reuse it with minor differences for different architectures or platforms.
        // note that during the creation of the fork, all elements (including arrays) replace the forkbase elements, however, the dictionary does not replace but "complements" as if mixing two objects and replacing only matching keys.
        // forks are also processed before filtering architectures, which allows, for example, to make a forkbase for a certain architecture and a fork for another, and for example, to replace the repository for downloading packages with a repository for another architecture.
        // if "forkArraysCombine" flag is set in builditem when creating a fork (not in forkbase!!!) When creating a fork, arrays do not overwrite but complement each other
        {
            "fork": true,
            "name": "custom-executable-alt1",

            "LDFLAGS": [
                "-alt-gcc-ldflags"
            ]
        },
        {
            "fork": true,
            "forkbase": true, //A builditem can be both a fork and a forkbase at the same time.
            "name": "custom-executable-alt2",

            "CFLAGS": [
                "-alt-gcc-cflags"
            ],

            "example_dictionary": {
                "inline_dictionary": {
                    "test1" : 1,
                    "test2" : 2,
                    "test3" : 3
                },
                "testArray": ["test1", "test2"],
                "test1" : 1,
                "test2" : 2,
                "test3" : 3
            }
        },
        {
            "fork": true, //here you fork the previous builditem because it is the closest forkbase

            "example_dictionary": {
                "inline_dictionary": {
                    "test2" : 7 //here you are replacing only test2 inside the inline_dictionary, you are not overwriting the rest of the keys inside the inline_dictionary
                },
                //here you have completely overwritten the array, that is, there will only be: ["test7", "test8"] in the array, and the old elements will disappear
                "testArray": ["test7", "test8"]
                //you also haven't touched any other elements inside the example_dictionary
            }
        },
        {
            "fork": true,

            // deleteBuildItemKeys will allow you to delete any tags inside the builditem along with the fork
            "deleteBuildItemKeys": [
                "CFLAGS"
            ],

            "example_dictionary": {
                // it also works for nested dicts
                "deleteBuildItemKeys": [
                    "inline_dictionary"
                ]
            }
        },
        {
            "fork": true,
            "forkArraysCombine": true,

            "example_dictionary": {
                // here you are not overwriting the old array, but rather adding elements to the end (thanks to the forkArraysCombine flag)
                // in this case, the array will contain: ["test1", "test2", "test7", "test8"]
                // NOT ["test7", "test8", "test7", "test8"], since the fork is not created from the previous builditem, but from the nearest previous one with the forkbase flag.
                "testArray": ["test7", "test8"]
            }
        },

        {
            "type": "build-configure-make",
            "name": "export",
            "export": false,

            "source": "builditem with source code",

            // specify the prefix. where will the program be installed as a result of the export
            "prefix": "/usr",

            // optional. allows you to use the directory as a sysroot for gcc
            "sysroot": "any builditem directory",

            // default: sysroot
            // with-sysroot for glibc
            "sysroot_field_name": "sysroot",

            // default: false
            // if set to true, sysroot will be passed directly to CFLAGS and LDFLAGS
            // needed to build util-linux
            "sysroot_gcc_direct": false,

            // default: false
            // if set to true, sysroot will be passed directly to gcc
            "sysroot_gcc_direct_cmd": false,

            // default: false
            "sysroot_gcc_env": false,

            // default: false
            // can be used with: sysroot_gcc_direct, sysroot_gcc_direct_cmd, sysroot_gcc_env
            "sysroot_gcc_disable_default": false,

            // default: false
            "sysroot_auto_libs": false,

            // default: false
            "sysroot_set_env_PKG_CONFIG_SYSROOT_DIR": false,

            // default: false
            "sysroot_set_env_PKG_CONFIG_LIBDIR": false,

            // default: false
            "disable_cross_compile": false,

            "env_change": {

            },

            "CFLAGS": [],
            "LDFLAGS": [],
            "CPPFLAGS": [],
            "CXXFLAGS": [],
            "FLAGS": [],
            "LIBS": []
        },

        {
            "type": "build-make",
            "name": "export",
            "export": false,

            "source": "builditem with source code",

            "prefix": "/usr",
            "sysroot": "any builditem directory",

            // default: false
            "disable_cross_compile": false,

            "make_args": [],
            "make_install_args": [],

            "env_change": {

            }
        },


        {
            "type": "directory",
            "name": "custom initramfs directory",
            "export": false,

            "items": [
                ["custom-executable", "/init"],
                ["just write text", "/text", [0, 0, "0644"], true]
            ]
        },
        {
            "type": "initramfs",
            "name": "custom initramfs.img",
            "export": false,

            "source": "custom initramfs directory"
        },
        {
            "type": "initramfs",
            "name": "compressed custom initramfs.img",
            "export": false,

            "source": "custom initramfs directory",
            "compressor": "gzip -9" //optional
        },

        // ---------------- making root fs
        {
            "type": "debian",
            "name": "debian directory",
            "export": false,

            "kernel": "default",
            "include": [
                "cowsay"
            ],

            "variant": "minbase",
            "suite": "bookworm",
            "url": "http://snapshot.debian.org/archive/debian/20250809T133719Z",
            
            // allows you to execute hook scripts when creating a system
            // automatically makes all files in the directory executable so that it doesn't have to be done manually after cloning the repository with the project
            // https://manpages.debian.org/unstable/mmdebstrap/mmdebstrap.1.en.html#hook
            // please note that the scripts are NOT executed inside the chroot, but on the host system.
            // to execute something inside the chroot, write in your script: chroot "$1" COMMAND
            // this will work even when cross-build to a different architecture. since mmdebstrap uses qemu for emulation, you can safely chroot there
            // however, please note that the cross-build may take a long time, and it may seem that the build has hung up, although this is not the case
            "hook-directory": "hooks"
        },
        {
            "type": "download",
            "name": "downloaded file",
            "export": false,

            "url": "https://raw.githubusercontent.com/igorkll/trashfolder/refs/heads/main/sound3/1.mp3"
        },
        {
            "type": "directory",
            "name": "rootfs directory",
            "export": false,

            // please note that although intermediate directories are created automatically, they will be created with access rights 0700 and not with the keys of the item/directory being created

            "move": [
                ["/bin", "/usr/bin"],
            ],

            "symlinks": [
                ["/usr/bin", "/bin"],
            ],

            "deleteBeforeAdd": [
                // at this stage, you can delete unnecessary files or directories
                // for example, you can build one system and want to use it in the second initrd, for example, for recovery mode
                // in this case, you will no longer need the initrd and the kernel in it, so delete them
                //"/any path"
            ],

            "directories": [
                // empty directories that will be created before adding items can be listed here
                // this is not necessary, since all directories are created automatically when adding items, but it can be used if you need an empty directory
                ["/home/MY EMPTY DIR", [0, 0, "0755"]]
            ],

            "items": [
                // adding the previously built debian to the file system
                // you can also import files/directories from your project's directory by simply specifying their name here
                // items of the build added to syslbuild itself will take precedence, but if there is no build item with that name, then syslbuild will try to import the file/directory from the project folder
                // when importing user files/directories, all UIDs and GIDs are default set to 0 and all access rights are set to 0700
                // this is done so that the build result is the same when cloning the repository from the version control system
                // when adding an item, you can specify your UID/GID and access rights, if you do not do this, then for user files from the project folder they will automatically be changed to zero (as mentioned above) and for previously collected items they will be moved unchanged
                // please note that this way you specify access rights recursively for all item elements, if you need a different behavior, then you must change it in a separate "chmod" block
                // ["file/dir in project | item name", "output path", [UID, GID, CHMOD]]
                // i recommend always explicitly specifying access rights, except when they are already set in the item (for example, when building debian, the rights are taken from packages)
                ["debian directory", "."],
                ["downloaded file", "/home/test.mp3", [0, 0, "0755"]],
                ["userfile.txt", "/home/userfile.txt", [0, 0, "0755"]], //file from the project folder
                ["other directory with non-executable files", ".", [[0, 0, "0644"], [0, 0, "0755"]]] //you can specify permissions first for files and then for directories.
            ],

            "move_after_items": [
                ["/bin", "/usr/bin"],
            ],

            "symlinks_after_items": [
                ["/usr/bin", "/bin"],
            ],

            "chmod": [
                // allows you to change access rights in the filesystem
                // first, specify the path to the object, then the new access rights (symbolic entry option is supported) and then a recursion flag if needed
                ["/home/MY EMPTY DIR", "1777", false] //let's say I want it to be a shared folder
            ],

            "chown": [
                ["/home/MY EMPTY DIR", 0, 0, false]
            ],

            "delete": [
                // at this stage, you can delete unnecessary files or directories
                // for example, you can build one system and want to use it in the second initrd, for example, for recovery mode
                // in this case, you will no longer need the initrd and the kernel in it, so delete them
                //"/any path"
            ]
        },

        

        // ---------------- arch linux example
        {
            "type": "arch-linux",
            "name": "arch directory",
            "export": true,

            "pacman_conf": {
                "options": {
                    "SigLevel": "Never"
                },
                "_auto": { //automatically replaced by core, extra, and community
                    "Server": "https://archive.archlinux.org/repos/2024/05/15/$repo/os/$arch"
                }
            },

            "include": [
                "base",
                "linux",
                "linux-firmware"
            ],
            "withoutDependencies": false
        },
        {
            "type": "arch-package",
            "name": "arch package",
            "export": true,

            "pacman_conf": {
                "options": {
                    "SigLevel": "Never"
                },
                "_auto": {
                    "Server": "https://archive.archlinux.org/repos/2024/05/15/$repo/os/$arch"
                }
            },

            "package": "linux",
            "withoutDependencies": false
        },

        // ---------------- packing root fs
        {
            "type": "filesystem",
            "name": "example-distro rootfs.img",
            "export": false,

            // specify the directory from which the filesystem will be created
            // this parameter is optional. you don't have to specify it if you need an empty file system.
            "source": "rootfs directory",

            "fs_type": "ext4",
            "size": "(auto * 1.2) + (100 * 1024 * 1024)", // could be a constant like 1G or 100M. when specified as auto, you operate with the value in bytes and can specify any eval
            "minsize": "64MB", //optional
            "label": "example-distro",

            // volume id for fat filesystem (optional)
            "fsid": "12345678",

            // uuid for ext* filesystem (optional)
            "fsid": "788384b6-7c84-42d3-bdb7-5101b201d24e",

            // revision for ext* filesystem (optional. It is not recommended for use)
            "revision": 1,

            //optional
            "chmod": [
                ["/", "1777", false]
            ],

            //optional
            "chown": [
                ["/", 0, 0, false]
            ],
        },
        {
            "type": "tar",
            "name": "example-distro rootfs.tar",
            "export": true,

            "source": "rootfs directory",

            "gz": false
        },
        {
            "type": "tar",
            "name": "example-distro rootfs.tar.gz",
            "export": true,

            "source": "rootfs directory",

            "gz": true
        },

        // ---------------- making full disk image (an image with an already installed system and bootloader, an OEM image that is usually installed on laptops at the factory. Whatever you want to call it)

        // ------ BIOS/MBR image
        {
            "type": "full-disk-image",
            "name": "example-distro MBR (BIOS).img",
            "export": true,

            // i am adding one megabyte (with a margin) for the partition table
            // since auto only takes into account the files size in bytes
            "size": "auto + (10 * 1024 * 1024)",

            // there are dos and gpt partition tables
            // sections have different types, and syslbuild has simpler aliases for names
            // although there's nothing stopping you from using dos partition IDs or UUIDs for gpt
            "partitionTable": "dos",
            "partitions": [
                ["example-distro rootfs.img", "linux"]
            ],

            "bootloader": {
                "type": "grub",
                "config": "grub.cfg", // grub.cfg from the project folder
                "boot": 0,
                "modules": [
                    "normal",
                    "part_msdos",
                    "part_gpt",
                    "ext2",
                    "configfile"
                ],

                // optional. you can pass additional arguments to grub-install
                // "install_extra_args": ["--disable-cli"]

                // you can force any grub target you are interested in
                // "target": "i386-efi"

                // if none of this is specified, the system grub will be installed (this is bad)
                // the path to the directory with grub builds. there should be grub builds inside for all the platforms that you need in the subdirectories.
                // "build": "path/to/you/grub/builds"
                // points to the directory of a specific assembly
                // "builddir": "path/to/you/grub/builds/i386-efi"
            }

            // do you want to use your grub target and still keep the project cross-compiled?
            // you can limit the build to specific architectures, and duplicate this block for each architecture.
            // "architectures": ["i386"]
        },

        // ------ BIOS/GPT image
        {
            "type": "filesystem",
            "name": "bios boot.img",
            "export": false,

            "size": "1M"
        },
        {
            "type": "full-disk-image",
            "name": "example-distro GPT (BIOS).img",
            "export": true,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["bios boot.img", "bios"],
                ["example-distro rootfs.img", "linux"]
            ],

            "bootloader": {
                "type": "grub",
                "config": "grub.cfg", // grub.cfg from the project folder
                "boot": 1,
                "modules": [
                    "normal",
                    "part_msdos",
                    "part_gpt",
                    "ext2",
                    "configfile"
                ]
            }
        },

        // ------ EFI/GPT image
        {
            "type": "filesystem",
            "name": "efi boot.img",
            "export": false,

            "fs_arg": "-F32",
            "fs_type": "fat",
            "size": "64M",
            "label": "EFI"
        },
        {
            "type": "full-disk-image",
            "name": "example-distro GPT (EFI).img",
            "export": true,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["efi boot.img", "efi"],
                ["example-distro rootfs.img", "linux"]
            ],

            "bootloader": {
                "type": "grub",
                "config": "grub.cfg", // grub.cfg from the project folder
                "esp": 0,
                "boot": 1,
                "modules": [
                    "normal",
                    "part_msdos",
                    "part_gpt",
                    "ext2",
                    "configfile"
                ]
            }
        },

        // ------ EFI+BIOS/GPT image (universal)
        {
            "type": "full-disk-image",
            "name": "example-distro GPT (EFI+BIOS).img",
            "export": true,

            "size": "auto + (10 * 1024 * 1024)",

            "partitionTable": "gpt",
            "partitions": [
                ["bios boot.img", "bios"],
                ["efi boot.img", "efi"],
                ["example-distro rootfs.img", "linux"]
            ],

            "bootloader": {
                "type": "grub",
                "config": "grub.cfg", // grub.cfg from the project folder
                "esp": 1,
                "boot": 2,
                "efiAndBios": true,
                "modules": [
                    "normal",
                    "part_msdos",
                    "part_gpt",
                    "ext2",
                    "configfile"
                ]
            }
        },

        // ------ build with uboot (example for ARM devices)
        {
            "type": "full-disk-image",
            "name": "my singleboard image.img",
            "export": true,

            "size": "auto + (16 * 1024 * 1024)",

            "partitionsStartSector": 8192,
            "partitionTable": "dos",
            "partitions": [
                ["my singleboard boot.img", "linux"],
                ["example-distro rootfs.img", "linux"]
            ],

            "bootloader": {
                "type": "binary",
                "binaries": [
                    {
                        "file": "my_uboot.bin",
                        "sector": 16
                    }
                ]
            }
        },

        // ---------------- creating an image for a singleboard

        // this is a simpler option than with a full-disk image
        // specifically, this example is for the orange pi zero 3
        {
            "type": "singleboard",
            "name": "my singleboard image 2.img",
            "export": true,

            // a mode compatible with your board must be selected
            "singleboardType": "uboot-offset",

            // the easiest way to get the bootloader is to get it from the original boot image. it is usually not only installed, but also lies as a separate file in the boot partition
            // due to the fact that the file size is extremely small, it can be stored in the project repository
            "bootloader": "u-boot-sunxi-with-spl.bin",
            "bootloader_offset": 16,
            
            "dtbList": [ //device tree
                "sun50i-h618-orangepi-zero3.dtb"
            ],
            "dtboList": [ //device tree overlays. optional
                "sun50i-h616-disable-leds.dtbo" //example
            ],

            // optional. 
            // you can use the uboot script.
            // you can transfer the already compiled .scr script or the source code .cmd and in this case it will be built automatically.
            // "uboot_script": "",

            // optional
            // add the necessary items to the boot partition directly
            "boot_part_items": [],

            // optional. default: extlinux/extlinux.conf
            "extlinux_path": "other.conf",

            "bootloaderDtb": "sun50i-h618-orangepi-zero3.dtb", //default dtb

            "kernel": "kernel.img",
            "initramfs": "initramfs.img", //optional
            "rootfs": "rootfs.img", //optional

            "boot_partition_minsize": "64MB", //optional
            "boot_partition_name": "BOOT",
            "boot_partition_size": "(auto * 1.2) + (100 * 1024 * 1024)",

            //optional
            "prepandPartitions": [
                ["example.img", "c"]
            ],

            //optional
            "appendPartitions": [
                ["example.img", "c"]
            ],

            "kernel_args_auto": true, //tells syslbuild to specify some kernel arguments itself, such as initrd=XXX
            //tells syslbuild to set root=XXX itself. rw/ro/manual
            //in manual mode, your kernel cmdline should already have rw/ro by default
            "kernel_rootfs_auto": "rw",
            "kernel_args": "rootwait console=ttyS0,115200 splash plymouth.ignore-serial-consoles",

            // you can redefine the name under which the kernel and initramfs will be located in the boot partition. by default, they have the same name as the original files.
            "kernel_filename_override": "kernel.img", //optional
            "initramfs_filename_override": "initramfs.img" //optional
        },

        // ---------------- some bootloaders can only load the kernel from the raw partition
        {
            "type": "from-directory",
            "name": "vmlinuz",
            "export": true,

            "source": "rootfs directory",
            "path": "/vmlinuz"
        },
        {
            "type": "from-directory",
            "name": "initrd.img",
            "export": true,

            // default: false
            // if true, the original access rights will be saved
            "save_rights": false,

            "source": "rootfs directory",
            "path": "/initrd.img"
        }

        // you can disassemble the initramdisk, for example, to rebuild it
        {
            "type": "unpack-initramfs",
            "name": "initrd directory",
            "export": false,

            "initramfs": "initrd.img",
            "decompressor": "cat" //zcat
        },

        // ---------------- easy creation of an iso image
        {
            "type": "grub-iso-image",
            "name": "lifeimage.iso",
            "export": true,

            // please note that you do not have a root file system here, your kernel and ramdisk must be able to work independently
            "kernel": "vmlinuz",
            "kernel_args": "quiet splash", //you can set custom kernel arguments if you want
            "initramfs": "initrd.img", //the parameter is optional and is not required if initramdisk is embedded in the kernel
            "show_boot_process": false, //shows the download output. does not work with config parameters
            "config": "config.cfg" //if you specify your config, the kernel_args and show_boot_process parameters will not work, since the kernel parameters are set in your config
        },

        // ---------------- creating your own custom core
        {
            "architectures": ["amd64"],
            "forkbase": true,

            "type": "kernel",
            "name": "custom_amd64_kernel",
            "export": false,

            // note that "headers_name" and "modules_name" should usually be installed in the /usr subdirectory inside rootfs and not in /

            "headers_name": "custom_amd64_kernel_headers",
            "headers_export": false,

            "modules_name": "custom_amd64_kernel_modules",
            "modules_export": false,

            "result_config_name": "custom_amd64_kernel_config",
            "result_config_export": false,

            "symvers_name": "Module.symvers",
            "symvers_export": true,

            // the url for downloading the kernel source code
            // single-board computers like the orange pi usually require their own core
            "kernel_source_url": "https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.18.7.tar.xz",
            // you can specify a custom unpacker for the kernel source code. by default "tar -xJf %s -C %s --strip-components=1"
            "kernel_source_unpacker": "tar -xJf %s -C %s --strip-components=1",

            // specify which file will be exported to builditem after the kernel build
            // syslbuild first searches for the file in "arch/<arch>/boot/<kernel_output_file>" and then in the root folder of the kernel project
            "kernel_output_file": "bzImage",

            // examples are taken from here: https://github.com/igorkll/linux-embedded-patchs
            // these are quite real patches, and they work
            "patches": [
                "disable_vt_swithing_from_keyboard.patch", // disables VT switching at the kernel level, but VT switching can still work from x11. it completely kills VT switching from the keyboard, but does not prevent VT switching from userspace (for example, via chvt). please note that if you disabled VT switching using the patch, it will only work in tty! switching processing can still occur at the graphics session level, it's easy to disable in x11, but it depends on the composer in wayland
                "disable_sysrq.patch", // it completely prohibits the operation of sysrq, regardless of the kernel parameters
                "disable_cad.patch", // blocks restarting by pressing ctrl+alt+del
                "disable_printk.patch" // will make the kernel shut up
            ],

            // optional. armbian build features
            "read_series_conf": [
                ["path/to/series.conf", "prefix/for/pathes/directory/"]
            ],

            "auto_patch_dt_makefile": [
                ["arch/arm/boot/dts/allwinner", "CONFIG_ARCH_SUNXI", true],
                ["arch/arm64/boot/dts/allwinner", "CONFIG_ARCH_SUNXI", true]
            ],

            // optional
            // execute commands from the source code directory of the kernel
            "pre_patches_commands": [
                "any shell command",
                "any shell command 2"
            ],

            "post_patches_commands": [
                "any shell command",
                "any shell command 2"
            ],

            // optional
            // if set to true, errors when applying patches will be ignored. This is done to apply whole bundles of patches at once (for example, from armbian) and let those that fit be applied
            // default: false
            "patches_ignore_errors": true,

            // optional
            // additional arguments for the patch program
            "patches_additional_args": "--fuzz=3",

            // optional. by default, syslbuild chooses defconfig itself based on the architecture for which it is being built. but you can specify it yourself.
            //"defconfig": "i386_defconfig",

            // optional. use custom kernel config
            "kernel_config": "my_kernel_config",

            "kernel_config_changes_files": [
                // you can list individual files with kernel config changes here
                // the format is the same as in the regular kernel config. comments are not taken into account, to disable some parameter, set it as =n
                "my_kernel_config_changes.txt"
            ],

            // local changes are more important than files
            "kernel_config_changes": [
                // these are standard changes to the kernel config that syslbuild makes by itself without saying anything unless the "kernel_config_disable_default_changes" parameter is set
                // he does this for the health of some of my patches.
                // ["CONFIG_WERROR", "n"],

                // for example, you can set the LOCALVERSION for the kernel
                // the values end up in the config as you describe them here. for this reason, you need to use the second quotation marks for the strings
                ["CONFIG_LOCALVERSION", "\"-custom\""],
                ["CONFIG_LOCALVERSION_AUTO", "n"]
            ],

            // if set to true, syslbuild will not make the standard kernel config changes that it makes
            // This list can be found above.
            "kernel_config_disable_default_changes": false,

            // if set to true, then before building the kernel, all =m in the config will be replaced with =y to get a self-sufficient kernel with embedded drivers.
            // default: False
            "kernel_config_embed_all_modules": false,

            // It allows you to copy files to the kernel directory before building. it may be necessary in some cases.
            // for example, sometimes when building a core for single-board devices, additional files are required for wifi to work
            // The ubuntu kernel may also require *.pem files to verify digital signatures.
            "items": [
                ["myproject/regulatory.db", "firmware/regulatory.db"]
            ],

            // unlike the usual "items", this one is copied only once and not with each build. either before patches or after patches
            "items_before_patches": [],
            "items_after_patches": [],

            // executes commands after "items_after_patches"
            "patches_complete_commands": [],

            // additional export files
            // you can export any files from the kernel project after the build
            // this can be used to export *.dtb files for ARM platforms
            // first, the path inside the kernel project is specified,
            // then the name of the exported object,
            // and then whether it needs to be exported to the output directory, making it available to the user.
            "additional_export": [
                ["arch/arm64/boot/dts/allwinner/sun50i-a64-pine64.dts", "sun50i-a64-pine64.dts", false],
                ["arch/arm64/boot/dts/allwinner/sun50i-h618-orangepi-zero3.dtb", "sun50i-h618-orangepi-zero3.dtb", false]
            ],

            "out_of_tree": false
        },
        {
            "type": "kernel",
            "name": "custom_kernel_from_git",
            "export": false,

            // you can get the kernel source code from the git repository
            "kernel_source_git": "https://github.com/armbian/linux",
            "kernel_source_git_branch": "example", //optional
            "kernel_source_git_checkout": "example" //optional
        },
        {
            // export new rootfs with initramfs, not initramfs
            // for it to work, the "source" must be debian with the "initramfs-tools" package

            "type": "debian-update-initramfs",
            "name": "rootfs-with-initramfs",
            "export": false,

            // the version of the kernel for which initramfs is being created
            "kernel_version": "6.18.7-custom", //it is optional if you have only one core in the system.

            // the rootfs (directory) where initramfs is created
            // this is not shown here, but the modules of the kernel for which you are generating initramfs should be installed in this rootfs
            // there should also be a "config-<kernel_version>" kernel config in the "/boot" directory, you can export the resulting kernel config with all changes via "result_config_name" in "kernel" builditem
            "source": "my_rootfs_with_kernel_modules" // your rootfs must have the "initramfs-tools" package and the kernel modules installed.
        },
        {
            // it works the same way as debian-update-initramfs, but accepts the kernel config separately (not required if the config is already in your rootfs) and exports initramfs itself, not the entire rootfs with it

            "type": "debian-export-initramfs",
            "name": "initramfs.img",
            "export": false,

            // you can export the resulting kernel config with all changes via "result_config_name" in "kernel" builditem
            "kernel_config": "kernel_config",
            "kernel_version": "6.18.7-custom", //it is optional if you have only one core in the system.
            "source": "my_rootfs_with_kernel_modules" // your rootfs must have the "initramfs-tools" package and the kernel modules installed.
        }
        {
            "architectures": ["amd64"],
            "fork": true, 

            "name": "custom_amd64_debug_kernel",
            "headers_name": "custom_amd64_debug_kernel_headers",
            "modules_name": "custom_amd64_debug_kernel_modules",

            "patches": [
                "disable_vt_swithing_from_keyboard.patch",
                "disable_sysrq.patch",
                "disable_cad.patch"
                // you can build two kernels, one for debugging and one for release
                // and use a different set of patches for them
                // due to the fact that syslbuild first downloads the kernel sources and then copies them for each build, there will be no patch conflicts
                // "disable_printk.patch"
            ]
        },
        {
            // perhaps you want a different kernel configuration to be used for a particular architecture. you can do this by combining fork and architectures.
            "architectures": ["arm64"],
            "fork": true, 

            "name": "custom_arm64_kernel",
            "headers_name": "custom_arm64_kernel_headers",
            "modules_name": "custom_arm64_kernel_modules",

            "kernel_config": "my_arm_kernel_config"
        },
        {
            "architectures": ["arm64"],
            "fork": true, 

            "name": "custom_arm64_debug_kernel",
            "headers_name": "custom_arm64_debug_kernel_headers",
            "modules_name": "custom_arm64_debug_kernel_modules",

            "kernel_config": "my_arm_kernel_config",

            "patches": [
                "disable_vt_swithing_from_keyboard.patch",
                "disable_sysrq.patch",
                "disable_cad.patch"
                // "disable_printk.patch"
            ]
        },

        // ---------------- 
        {
            "type": "patches",
            "name": "after_patches",
            "export": false,

            "source": "before_patches",

            "patches": [
                "disable_vt_swithing_from_keyboard.patch",
                "disable_sysrq.patch",
                "disable_cad.patch",
                "disable_printk.patch"
            ],

            // optional
            // execute commands from the directory
            "pre_patches_commands": [
                "any shell command",
                "any shell command 2"
            ],

            "post_patches_commands": [
                "any shell command",
                "any shell command 2"
            ],

            "items_before_patches": [],
            "items_after_patches": [],

            // executes commands after "items_after_patches"
            "patches_complete_commands": [],

            // optional
            // default: false
            "patches_ignore_errors": true,

            // optional
            // additional arguments for the patch program
            "patches_additional_args": "--fuzz=3",
        }

        // ---------------- template example


        {
            "forkbase": true,
            "template": true, // template means that this builditem itself will not be assembled

            "type": "kernel",
            "name": "bzImage",
            "export": false,

            "headers_name": "kernel_headers",
            "headers_export": false,

            "modules_name": "kernel_modules",
            "modules_export": false,

            "kernel_source_url": "https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.18.7.tar.xz",
            "kernel_output_file": "bzImage",
        },
        {
            "fork": true,
            "architectures": ["amd64"],
            "kernel_config": "kernel_config_amd64"
        },
        {
            "fork": true,
            "architectures": ["arm64"],
            "kernel_config": "kernel_config_arm64"
        },

        // -----------------

        // executes all the scripts listed in the list inside the chroot. it will copy qemu-static itself if necessary
        // he performs the necessary bindings himself so that the script runs correctly
        // exports a new rootfs with scripts executed inside the chroot
        {
            "type": "smart-chroot",
            "name": "my_rootfs_with_chroot_scripts_changes",
            "export": false,

            "source": "my_rootfs",
            "scripts": [
                "script_in_project.sh",
                "script_in_project_2.sh"
            ],

            // disables the armel and armhf assembly fix. it can be used if the bug is fixed in qemu-static/glibc
            "disable_shitfix_armel_armhf_build": false
        },

        // runs the script via "systemd-nspawn" in the systemd-container. it is necessary if you will interact with systemd inside the container (for example, you need to change its settings)
        {
            "type": "smart-chroot",
            "name": "my_rootfs_with_chroot_scripts_changes",
            "export": false,

            "use_systemd_container": true,
            "fix_systemd_container_host_files_copy": true,

            // default: false
            // I highly recommend enabling this for "use_systemd_container" because if your script fails, the build will continue as if there were no errors.
            // if you enable this option, then in each of your chroot scripts you must create a file or directory along the path "/.chrootend", syslbuild will delete it and consider that everything is fine.
            // if there is no file or directory on this path, the build will fail.
            "manual_validation": false,

            "source": "my_rootfs",
            "scripts": [
                "script_in_project.sh",
                "script_in_project_2.sh"
            ]
        },

        // You can also set different startup parameters for different scripts.
        {
            "type": "smart-chroot",
            "name": "my_rootfs_with_chroot_scripts_changes",
            "export": false,

            "source": "my_rootfs",
            "scripts": [
                // path, use_systemd_container, manual_validation
                ["script_in_project.sh", false, false], //chroot script
                ["script_in_project_2.sh", true, true], //systemd-nspawn script with manual validation
                ["script_in_project_3.sh", true, false] //systemd-nspawn script without manual validation
            ]
        },

        {
            "type": "gitclone",
            "name": "gitclone_repo",
            "export": false,

            "git_url": "https://github.com/armbian/linux",
            "git_branch": "example", //optional
            "git_checkout": "example" //optional
        },

        // filter builditem examples
        {
            // this builditem will only be built if at least one filter is specified
            // example:
            // --filters debug
            // --filters test,wayland
            "type": "gcc-build",
            "name": "example1",

            "build-if-filter-exists": true
        },
        {
            // this builditem will only be built if NO filters are specified
            // example:
            // ./build.py --arch amd64 project.json
            "type": "gcc-build",
            "name": "example2",

            "build-if-filter-not-exists": true
        },
        {
            // this builditem will only be built if ALL specified filters exist
            // required filters:
            // debug AND wayland
            //
            // works:
            // --filters debug,wayland
            // --filters debug,wayland,test
            //
            // does NOT work:
            // --filters debug
            // --filters wayland
            "type": "gcc-build",
            "name": "example3",

            "build-if-all-filters-exists": [
                "debug",
                "wayland"
            ]
        },
        {
            // this builditem will be built if AT LEAST ONE filter exists
            //
            // works:
            // --filters debug
            // --filters test,wayland
            //
            // does NOT work:
            // --filters release
            "type": "gcc-build",
            "name": "example4",

            "build-if-one-filter-exists": [
                "debug",
                "wayland"
            ]
        },
        {
            // this builditem will NOT be built
            // if ALL specified filters exist at the same time
            //
            // blocked:
            // --filters debug,wayland
            //
            // works:
            // --filters debug
            // --filters wayland
            // --filters release
            "type": "gcc-build",
            "name": "example5",

            "build-if-not-all-filters-exists": [
                "debug",
                "wayland"
            ]
        },
        {
            // this builditem will NOT be built
            // if AT LEAST ONE specified filter exists
            //
            // blocked:
            // --filters debug
            // --filters wayland
            // --filters test,debug
            //
            // works:
            // --filters release
            // no filters
            "type": "gcc-build",
            "name": "example6",

            "build-if-not-one-filter-exists": [
                "debug",
                "wayland"
            ]
        }
    ]
}
```