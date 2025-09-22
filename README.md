# syslbuild
an build system for creating Linux distributions. it is focused on embedded distributions 
DOWNLOAD THE RELEASE, NOT THE REPOSITORY!
* the program requires root access because it mounts images
* if you don't want to run this on the host system to avoid providing root access, you can run this in a container
* syslbuild allows you to automate the distribution build process, which is suitable for small custom distributions
* syslbuild is focused on building distributions for embedded systems (kiosks, navigators, and DVRs)
* in syslbuild, the build process is described by writing json with individual build elements (filesystems, kernels, bootloaders)
* syslbuild is able to create a boot image with a partition table itself, which can be convenient for creating a complete firmware.

## build process
you create a folder and in it a json file with a description of the project  
it describes the build items, each of which can be 'exported' and/or used in another build items  
if you set the 'export' flag to true in the build item, the build item will appear in the output directory after the build, otherwise it will remain in .temp but can be used for other build items during the build process  
for example, for a phone whose bootloader usually loads the kernel from the raw partition, you can separately assemble the rootfs and the kernel separately and export them separately  
for a computer, you can build a kernel, but not export it, but assemble the debian base system separately. after create a file system, copy debian and the kernel into it, and then add another build item that will make an img with a bootloader and MBR  
the build in syslbuild is heavily divided into items, for example, you can't just assemble a module into a file system. First, you need to create a separate item directory and then add it to the file system  
also, assembling a bootable img with an already installed system is also a separate build item in which you must add file systems, etc  

## dependencies
* python3
* mmdebstrap
* mkfs.* - you need support for the file systems that you intend to use in your projects
* qemu - needed for debian cross-build
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

## python dependencies
* json5
* asteval

## installing dependencies on debian systems (or you can use venv)
* sudo apt install mmdebstrap
* sudo pip install json5 --break-system-packages
* sudo pip install asteval --break-system-packages

## build items types
* debian - debian build via mmdebstrap
* download - downloads the file
* directory - allows you to assemble many items into one (for example, to pack them into a file system later) allows you to set file owners and their rights
* filesystem - builds a file system from the specified items and sets the specified access rights for the files
* tar - collects archive from directory in tar format
* full-disk-image - creates a bootable image of a raw img disk that can be written to the root of the disk via dd or some etcher and it will immediately become bootable (the ability to boot depends on the settings)
* kernel - 
* initramfs - 

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

## project example
```json
{
    "min-syslbuild-version": [0, 1, 0],

    "builditems": [
        {
            "type": "debian",
            "name": "debian directory",
            "export": false,

            "kernel": "default",
            "include": [
                "cowsay"
            ],
            "exclude": [],

            "variant": "minbase",
            "suite": "bookworm",
            "url": "http://snapshot.debian.org/archive/debian/20250809T133719Z"
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
                "/home/MY EMPTY DIR"
            ],

            "items": [
                // adding the previously built debian to the file system
                // you can also import files/directories from your project's directory by simply specifying their name here
                // items of the build added to syslbuild itself will take precedence, but if there is no build item with that name, then syslbuild will try to import the file/directory from the project folder
                // when importing user files/directories, all UIDs and GIDs are automatically set to 0 and all access rights are set to 0000
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
            }
        },

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
        }
    ]
}
```