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


