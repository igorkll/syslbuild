#!/bin/bash

# ------------- mounts
mkdir -p /data
mount -n -o move /updateroot/data /data

boot_dev=$(findmnt -nro SOURCE /updateroot/bootmnt)
rootfs_dev=$(findmnt -nro SOURCE /updateroot)

image_path=$(cat /updateroot/updatescript/path)

umount /updateroot/bootmnt
umount /updateroot

# ------------- find partitions in image

partitiontable=$(sfdisk -J "$image_path")

sector_size=$(echo "$partitiontable" | jq -r '.partitiontable.sectorsize')

image_boot_start=$(echo "$partitiontable" | jq '.partitiontable.partitions[] | select(.name=="BOOT") | .start')
image_boot_size=$(echo "$partitiontable" | jq '.partitiontable.partitions[] | select(.name=="BOOT") | .size')

image_rootfs_start=$(echo "$partitiontable" | jq '.partitiontable.partitions[] | select(.name=="rootfs") | .start')
image_rootfs_size=$(echo "$partitiontable" | jq '.partitiontable.partitions[] | select(.name=="rootfs") | .size')

# ------------- get real partitions info

boot_size=$(blockdev --getsize "$boot_dev" 2>/dev/null)
rootfs_size=$(blockdev --getsize "$rootfs_dev" 2>/dev/null)

if [ -n "$image_boot_size" ] && [ -n "$boot_dev" ]; then
    if [ "$image_boot_size" -gt "$boot_size" ]; then
        echo "BOOT partition in image is bigger than target"
        exit 1
    fi
fi

if [ -n "$image_rootfs_size" ] && [ -n "$rootfs_dev" ]; then
    if [ "$image_rootfs_size" -gt "$rootfs_size" ]; then
        echo "ROOTFS partition in image is bigger than target"
        exit 1
    fi
fi

# ------------- flash new partitions

if [ -n "$boot_dev" ]; then
    if [ -z "$image_boot_start" ]; then
        echo there are no boot partition in the image
        exit 1
    fi
    dd if="$image_path" of="$boot_dev" bs=$sector_size skip=$image_boot_start count=$image_boot_size
fi

if [ -n "$rootfs_dev" ]; then
    if [ -z "$image_rootfs_start" ]; then
        echo there are no rootfs partition in the image
        exit 1
    fi
    dd if="$image_path" of="$rootfs_dev" bs=$sector_size skip=$image_rootfs_start count=$image_rootfs_size
fi
