# mount_external_drives
## demonstration of liamounts integration into the system image
liamounts: https://github.com/igorkll/liamounts/tree/main  
liamounts automatically mounts all external drives to "/automounts". He mounts disks that support unix access rights via bindfs so that these rights are ignored and users without root have full access to the contents of disks with the ext4 file system.  

## ProgramLoader
as a "Payload", the system has a simple launcher for programs from external media  
it can load the following files from an attached USB flash drive:  
* programloader - executable file
* video.mp4 - video
* audio.mp3 - audio
to stop the program or restore it, it is enough to pull out the USB flash drive  
