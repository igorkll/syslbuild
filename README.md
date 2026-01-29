# syslbuild 0.3.0
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

## you may also be interested in
* https://github.com/igorkll/linux-embedded-patchs - a set of patches for using the linux kernel on embedded locked-down devices
* https://github.com/igorkll/WinBox-Maker - a program for creating embedded Windows images

## build process
you create a folder and in it a json file with a description of the project  
it describes the build items, each of which can be 'exported' and/or used in another build items  
if you set the 'export' flag to true in the build item, the build item will appear in the output directory after the build, otherwise it will remain in .temp but can be used for other build items during the build process  
for example, for a phone whose bootloader usually loads the kernel from the raw partition, you can separately assemble the rootfs and the kernel separately and export them separately  
for a computer, you can build a kernel, but not export it, but assemble the debian base system separately. after create a file system, copy debian and the kernel into it, and then add another build item that will make an img with a bootloader and MBR  
the build in syslbuild is heavily divided into items, for example, you can't just assemble a module into a file system. First, you need to create a separate item directory and then add it to the file system  
also, assembling a bootable img with an already installed system is also a separate build item in which you must add file systems, etc  

## arguments
* -h - show help info
* --arch ARCHITECTURE - set the output architecture of the build
* -n - does the build anew, does not use the cache (syslbuild caches the kernel source code anyway, even in this mode. use -d if you want to download the kernel again)
* -d - do not use the download cache of the kernel sources

## dependencies
* python3
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

## docs
* mmdebstrap: https://manpages.debian.org/testing/mmdebstrap/mmdebstrap.1.en.html

## python dependencies
* json5
* asteval

## installing dependencies on debian systems (or you can use venv)
* sudo apt install mmdebstrap
* sudo pip install json5 --break-system-packages
* sudo pip install asteval --break-system-packages

## build items types
* debian - debian build via mmdebstrap
* arch-linux - arch linux build via pacstrap (It's not working right now)
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

## aliases of names for partitions IDs (GPT / MBR)
* linux - 0FC63DAF-8483-4772-8E79-3D69D8477DE4 / 83
* swap - 0657FD6D-A4AB-43C4-84E5-0933C84B4F4F / 82
* efi - C12A7328-F81F-11D2-BA4B-00A0C93EC93B / ef
* bios - 21686148-6449-6E6F-744E-656564454649 / None

## debian kernel types
* default
* realtime

## builditem universal keys
* architectures - if the builditem has an array with that name, then the build will only be performed if it has an architecture for which it is being built
* forkbase - this element becomes the base for creating forks
* fork - it takes as a basis (forks) the nearest previous element from forkbase. When dictionaries merge, the matching keys (including arrays) overwrite each other. if the forkArraysCombine flag is set when creating a fork (not in forkbase!!!) the arrays do not overwrite each other, but complement each other.
* forkArraysCombine - if this flag is set in builditem when creating a fork (not in forkbase!!!) When creating a fork, arrays do not overwrite but complement each other. by default, this flag has the value false.
* template - this key is used to exclude any builditem from the build. created for use with forkbase. if you set it to true, this element will not participate in the build, but it can still be forked via forkbase. this tag is not inherited during fork

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
* full disk image | with graphic | x86_64 | BIOS: qemu-system-x86_64 \
  -m 2048 -smp 4 \
  -device virtio-gpu \
  -vga virtio \
  -drive file=output/amd64/disk.img,format=raw
* full disk image | with graphic | x86_64 | UEFI: qemu-system-x86_64 \
  -m 2048 -smp 4 \
  -device virtio-gpu \
  -vga virtio \
  -drive file=output/amd64/disk.img,format=raw \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=output/OVMF_VARS.fd
* iso image | x86 | BIOS: qemu-system-i386 -cdrom output/i386/lifeimage.iso -boot d -m 2048

## roadmap
* add the ability to add additional files to the iso images
* the ability to specify changes for kernel config parameters directly in the builditem of the kernel build
* exporting the resulting kernel config when building the kernel
* support for the operation (packing and unpacking) of initramfs with a multiblock structure
* built-in export support for popular single-boarders and pine phone and librem 5. I want to make a builditem that downloads the bootloader for the specified single-board itself and builds the image using the transferred kernel, rootfs, initramfs and settings

## roadmap completed
* execution of arbitrary scripts in the system's chroot, with qemu-static support for execution during assembly for a different architecture
* make a normal caching system

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
        // ---------------- building custom executable
        {
            "type": "gcc-build",
            "name": "custom-executable",
            "export": false,

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
            
            "forkbase": true //marking the builditem as the base for creating forks
        },
        // you can create forks, and even multiple forks from a single forkbase. This can be used, for example, for cross-assembly, to set up the assembly of some complex element once and then reuse it with minor differences for different architectures or platforms.
        // note that during the creation of the fork, all elements (including arrays) replace the forkbase elements, however, the dictionary does not replace but "complements" as if mixing two objects and replacing only matching keys.
        // forks are also processed before filtering architectures, which allows, for example, to make a forkbase for a certain architecture and a fork for another, and for example, to replace the repository for downloading packages with a repository for another architecture.
        // if forkArraysCombine flag is set in builditem when creating a fork (not in forkbase!!!) When creating a fork, arrays do not overwrite but complement each other
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
            "forkArraysCombine": true,

            "example_dictionary": {
                // here you are not overwriting the old array, but rather adding elements to the end (thanks to the forkArraysCombine flag)
                // in this case, the array will contain: ["test1", "test2", "test7", "test8"]
                // NOT ["test7", "test8", "test7", "test8"], since the fork is not created from the previous builditem, but from the nearest previous one with the forkbase flag.
                "testArray": ["test7", "test8"]
            }
        },

        {
            "type": "directory",
            "name": "custom initramfs directory",
            "export": false,

            "items": [
                ["custom-executable", "/init"]
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

            "directories": [
                // empty directories that will be created before adding items can be listed here
                // this is not necessary, since all directories are created automatically when adding items, but it can be used if you need an empty directory
                ["/home/MY EMPTY DIR", [0, 0, "0755"]]
            ],

            "items": [
                // adding the previously built debian to the file system
                // you can also import files/directories from your project's directory by simply specifying their name here
                // items of the build added to syslbuild itself will take precedence, but if there is no build item with that name, then syslbuild will try to import the file/directory from the project folder
                // when importing user files/directories, all UIDs and GIDs are default set to 0 and all access rights are set to 0000
                // this is done so that the build result is the same when cloning the repository from the version control system
                // when adding an item, you can specify your UID/GID and access rights, if you do not do this, then for user files from the project folder they will automatically be changed to zero (as mentioned above) and for previously collected items they will be moved unchanged
                // please note that this way you specify access rights recursively for all item elements, if you need a different behavior, then you must change it in a separate "chmod" block
                // ["file/dir in project | item name", "output path", [UID, GID, CHMOD]]
                // i recommend always explicitly specifying access rights, except when they are already set in the item (for example, when building debian, the rights are taken from packages)
                ["debian directory", "."],
                ["downloaded file", "/home/test.mp3", [0, 0, "0755"]],
                ["userfile.txt", "/home/userfile.txt", [0, 0, "0755"]] //file from the project folder
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
            "label": "example-distro"
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
            "size": "auto + (1 * 1024 * 1024)",

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
                ]
                // you can force any grub target you are interested in
                // "target": "i386-efi"
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

            "size": "auto + (1 * 1024 * 1024)",

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

            "size": "auto + (1 * 1024 * 1024)",

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

            "size": "auto + (1 * 1024 * 1024)",

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

            // optional. by default, syslbuild chooses defconfig itself based on the architecture for which it is being built. but you can specify it yourself.
            //"defconfig": "i386_defconfig",

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
        },
        {
            // export new rootfs with initramfs, not initramfs
            // for it to work, the "source" must be debian with the "initramfs-tools" package

            "type": "debian-update-initramfs",
            "name": "rootfs-with-initramfs",
            "export": false,

            // the version of the kernel for which initramfs is being created
            "kernel_version": "6.18.7-custom",

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
            "kernel_version": "6.18.7-custom",
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
            ]
        }
    ]
}
```