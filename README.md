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
* mkfs.*

## python dependencies
* json5
* asteval

## installing dependencies on debian systems (or you can use venv)
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
                // adding the previously built debian to the file system
                // you can also import files/directories from your project's directory by simply specifying their name here
                // items of the build added to syslbuild itself will take precedence, but if there is no build item with that name, then syslbuild will try to import the file/directory from the project folder
                // when importing user files/directories, all UIDs and GIDs are automatically set to 0 and all access rights are set to 0000
                // this is done so that the build result is the same when cloning the repository from the version control system
                // when adding an item, you can specify your UID/GID and access rights, if you do not do this, then for user files from the project folder they will automatically be changed to zero (as mentioned above) and for previously collected items they will be moved unchanged
                // please note that this way you specify access rights recursively for all item elements, if you need a different behavior, then you must change it in a separate "chmod" block
                // ["file/dir in project | item name", "output path", [UID, GID, CHMOD]]
                ["debian folder", "."]
                // ["userfile.txt", "/home/userfile.txt", [0, 0, "0000"]]
            ],

            "chmod": [
                // allows you to change access rights in the filesystem
                // first, specify the path to the object, then the new access rights (symbolic entry option is supported) and then a recursion flag if needed
                ["/home/MY EMPTY DIR", "1777", false] //let's say I want it to be a shared folder
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