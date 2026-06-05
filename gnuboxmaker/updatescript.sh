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

image_boot_start=$(sfdisk -J "$image_path" | jq '.partitiontable.partitions[] | select(.name=="BOOT") | .start')
image_boot_size=$(sfdisk -J "$image_path" | jq '.partitiontable.partitions[] | select(.name=="BOOT") | .size')

image_rootfs_start=$(sfdisk -J "$image_path" | jq '.partitiontable.partitions[] | select(.name=="rootfs") | .start')
image_rootfs_size=$(sfdisk -J "$image_path" | jq '.partitiontable.partitions[] | select(.name=="rootfs") | .size')

# ------------- get real partitions info


# ------------- flash new partitions

if [ -n "$boot_dev" ]; then
    if [ -z "$boot_dev" ]; then
        echo there are no boot partition in the image
        exit 1
    fi
    dd if="$image_path" of="$boot_dev" bs=512 skip=$image_boot_start count=$image_boot_size
fi

if [ -n "$rootfs_dev" ]; then
    if [ -z "$rootfs_dev" ]; then
        echo there are no rootfs partition in the image
        exit 1
    fi
    dd if="$image_path" of="$rootfs_dev" bs=512 skip=$image_rootfs_start count=$image_rootfs_size
fi
