#!/bin/bash

if [ "$(id -u)" -ne 0 ]; then
    echo "Error: must be run as root"
    exit 1
fi

if ! mountpoint -q /data; then
    echo "Error: /data is not mounted"
    exit 1
fi

if [ $# -ne 1 ]; then
    echo "usage: $0 /path/to/new/firmware.img"
    exit 1
fi

BOOTIMAGE="$1"

if [ ! -f "$BOOTIMAGE" ]; then
    echo "Error: File not found $BOOTIMAGE"
    exit 1
fi

file_dev=$(stat -c %d "$BOOTIMAGE")
data_dev=$(stat -c %d /data)

if [ "$file_dev" -eq "$data_dev" ]; then
    mount -o remount,rw /

    rm -rf /updatescript
    mkdir /updatescript
    cp updatescript.sh /updatescript/updatescript.sh
    echo "$BOOTIMAGE" > /updatescript/path

    sync
    shutdown --no-wall now
else
    echo the self-updating file can ONLY be located on the DATA section partition
fi
