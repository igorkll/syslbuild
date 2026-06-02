#!/bin/bash

if [ $# -ne 1 ]; then
    echo "usage: $0 /path/to/new/firmware.img"
    exit 1
fi

BOOTIMAGE="$1"

if [ ! -f "$BOOTIMAGE" ]; then
    echo "File not found: $BOOTIMAGE"
    exit 1
fi


file_dev=$(stat -c %d "$BOOTIMAGE")
root_dev=$(stat -c %d /)
data_dev=$(stat -c %d /data)

if [ "$file_dev" -eq "$root_dev" ]; then
    mount -o remount,rw /

    mkdir /updatescript
    cp updatescript.sh /updatescript/updatescript.sh
else
    echo the update file must be located on the root partition or on the data partition
fi
