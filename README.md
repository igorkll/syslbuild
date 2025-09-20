# syslbuild
an assembly system for creating Linux distributions. it is focused on embedded distributions 
DOWNLOAD THE RELEASE, NOT THE REPOSITORY!
* the program requires root access because it mounts images

## build process
you create a folder and in it a json file with a description of the project  
it describes the build items, each of which can be 'exported' and/or used in another build items  
if you set the 'export' flag to true in the build item, the build item will appear in the output directory after the build, otherwise it will remain in .temp but can be used for other build items during the build process  
for example, for a phone whose bootloader usually loads the kernel from the raw partition, you can separately assemble the rootfs and the kernel separately and export them separately  
for a computer, you can build a kernel, but not export it, but assemble the debian base system separately. after create a file system, copy debian and the kernel into it, and then add another build item that will make an img with a bootloader and MBR  
the assembly in syslbuild is heavily divided into items, for example, you can't just assemble a module into a file system. First, you need to create a separate item directory and then add it to the file system  
also, assembling a bootable img with an already installed system is also a separate assembly item in which you must add file systems, etc  

## dependencies
* python3
* mmdebstrap
* mkfs.*

## python dependencies
* json5
* asteval

## installing dependencies on debian systems
* sudo apt install mmdebstrap
* sudo pip install json5 --break-system-packages
* sudo pip install asteval --break-system-packages

## project example
```json
{
    "builditems": [
        {
            "type": "debian",
            "name": "debian folder",
            "export": false,

            "include": [
                "cowsay"
            ],
            "exclude": [],

            "variant": "minbase",
            "suite": "bookworm",
            "url": "http://snapshot.debian.org/archive/debian/20250809T133719Z"
        },
        {
            "type": "filesystem",
            "name": "example-distro rootfs.img",
            "export": false,

            "directories": [
                // empty directories that will be created before adding items can be listed here
                // this is not necessary, since all directories are created automatically when adding items, but it can be used if you need an empty directory
                "/home/MY EMPTY DIR"
            ],

            "items": [
                ["debian folder", "."] //adding the previously built debian to the file system
            ],

            "fs_type": "ext4",
            "size": "(auto * 1.2) + (100 * 1024 * 1024)", //could be a constant like 1G or 100M. when specified as auto, you operate with the value in bytes and can specify any eval
            "label": "example-distro"
        },
        {
            "type": "full-disk-image",
            "name": "example-distro.img",
            "export": true,

            "items": [
                
            ]
        }
    ]
}
```