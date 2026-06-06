#!/bin/bash

# ------------- mounts

echo "start self update"

mkdir -p /data
mount -n -o move /updateroot/data /data

boot_dev=$(findmnt -nro SOURCE /updateroot/bootmnt)
rootfs_dev=$(findmnt -nro SOURCE /updateroot)
echo "boot device: $boot_dev"
echo "rootfs device: $rootfs_dev"

image_path=$(cat /updateroot/updatescript/path)
echo "update from image $image_path"

echo "unmounting /updateroot/bootmnt"
umount /updateroot/bootmnt

echo "unmounting /updateroot"
umount /updateroot

# ------------- find partitions in image

partitiontable=$(sfdisk -J "$image_path")

sector_size=$(echo "$partitiontable" | jq -r '.partitiontable.sectorsize')

# image_boot_start=$(echo "$partitiontable" | jq '.partitiontable.partitions[] | select(.name=="BOOT") | .start')
# image_boot_size=$(echo "$partitiontable" | jq '.partitiontable.partitions[] | select(.name=="BOOT") | .size')

# image_rootfs_start=$(echo "$partitiontable" | jq '.partitiontable.partitions[] | select(.name=="rootfs") | .start')
# image_rootfs_size=$(echo "$partitiontable" | jq '.partitiontable.partitions[] | select(.name=="rootfs") | .size')

if [ -n "$boot_dev" ] && [ -n "$rootfs_dev" ]; then
    image_boot_start=$(echo "$partitiontable" | jq '.partitiontable.partitions[0].start')
    image_boot_size=$(echo "$partitiontable" | jq '.partitiontable.partitions[0].size')

    image_rootfs_start=$(echo "$partitiontable" | jq '.partitiontable.partitions[1].start')
    image_rootfs_size=$(echo "$partitiontable" | jq '.partitiontable.partitions[1].size')
elif [ -n "$rootfs_dev" ]; then
    image_rootfs_start=$(echo "$partitiontable" | jq '.partitiontable.partitions[0].start')
    image_rootfs_size=$(echo "$partitiontable" | jq '.partitiontable.partitions[0].size')
fi

echo "partitiontable: $partitiontable"
echo "sector_size: $sector_size"
echo "image_boot_start: $image_boot_start"
echo "image_boot_size: $image_boot_size"
echo "image_rootfs_start: $image_rootfs_start"
echo "image_rootfs_size: $image_rootfs_size"

# ------------- get real partitions info

boot_size=$(blockdev --getsize "$boot_dev")
rootfs_size=$(blockdev --getsize "$rootfs_dev")

echo "boot_size: $boot_size"
echo "rootfs_size: $rootfs_size"

if [ -n "$image_boot_size" ] && [ -n "$boot_dev" ]; then
    if [ "$image_boot_size" -gt "$boot_size" ]; then
        echo "BOOT partition in image is bigger than target"
        exit 1
    fi
fi

if [ -n "$image_rootfs_size" ] && [ -n "$rootfs_dev" ]; then
    if [ "$image_rootfs_size" -gt "$rootfs_size" ]; then
        echo "rootfs partition in image is bigger than target"
        exit 1
    fi
fi

# ------------- flash new partitions

if [ -n "$boot_dev" ] && [ -z "$image_boot_start" ]; then
    echo there are no BOOT partition in the image
    exit 1
fi

if [ -n "$rootfs_dev" ] && [ -z "$image_rootfs_start" ]; then
    echo there are no rootfs partition in the image
    exit 1
fi

if [ -n "$boot_dev" ]; then
    echo "start writing BOOT partition..."
    dd if="$image_path" of="$boot_dev" bs=$sector_size skip=$image_boot_start count=$image_boot_size status=progress conv=fsync
fi

if [ -n "$rootfs_dev" ]; then
    echo "start writing rootfs partition..."
    dd if="$image_path" of="$rootfs_dev" bs=$sector_size skip=$image_rootfs_start count=$image_rootfs_size status=progress conv=fsync
fi
