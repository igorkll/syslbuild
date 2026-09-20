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
    echo "File not found $BOOTIMAGE"
    exit 1
fi

file_dev=$(stat -c %d "$BOOTIMAGE")
data_dev=$(stat -c %d /data)

if [ "$file_dev" -eq "$data_dev" ]; then
    if [[ "$BOOTIMAGE" != /data/* ]]; then
        BOOTIMAGE="/data$(realpath "$BOOTIMAGE")"
    fi

    if [ ! -f "$BOOTIMAGE" ]; then
        echo "File after path resolving not found $BOOTIMAGE"
        exit 1
    fi

    rm -rf /data/.post_update_processed.flag
    rm -rf /data/.private/updatescript
    mkdir /data/.private/updatescript
    cp /gnubox/updatescript.sh /data/.private/updatescript/updatescript.sh
    echo "$BOOTIMAGE" > /data/.private/updatescript/path

    sync
    shutdown --no-wall -r now
else
    echo the self-updating file can ONLY be located on the DATA section partition
fi
