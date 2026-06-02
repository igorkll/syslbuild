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


