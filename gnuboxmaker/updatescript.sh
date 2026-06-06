#!/bin/bash

# ------------- copy script to tmp

if [ "${0#/tmp/}" = "$0" ]; then
    echo "Moving self-update script to /tmp"
    cp "$0" /tmp/updatescript.sh
    chmod +x /tmp/updatescript.sh
    exec /tmp/updatescript.sh "$@"
fi

# ------------- mounts

echo "START SELF-UPDATE..."

mkdir -p /data
mount -n -o move /updateroot/data /data

boot_dev=$(findmnt -nro SOURCE /updateroot/bootmnt)
rootfs_dev=$(findmnt -nro SOURCE /updateroot)
echo "boot device: $boot_dev"
echo "rootfs device: $rootfs_dev"

image_path=$(cat /updateroot/updatescript/path)
echo "update from image $image_path"

echo "unmounting /updateroot/bootmnt"
/nativeumount -fR /updateroot/bootmnt

echo "unmounting /updateroot"
/nativeumount -fR /updateroot

sync

# ------------- find partitions in image

partitiontable=$(sfdisk -J "$image_path")

sector_size=$(echo "$partitiontable" | jq -r '.partitiontable.sectorsize')

bios_start_part=$(echo "$partitiontable" | jq -r '
  .partitiontable.partitions[]
  | select(.type == "21686148-6449-6E6F-744E-656564454649")
  | .start
')

efi_start_part=$(echo "$partitiontable" | jq -r '
  .partitiontable.partitions[]
  | select(.type == "C12A7328-F81F-11D2-BA4B-00A0C93EC93B")
  | .start
')

echo "bios_start_part: $bios_start_part"
echo "efi_start_part: $efi_start_part"

# как блять сделать работу на export_img_bios_gpt, export_img_uefi_gpt, export_img_bios_and_uefi_gpt
# поправочка: ну вроде должно работать

if { [ "$efi_start_part" != "null" ] && [ -n "$efi_start_part" ]; } \
&& { [ "$bios_start_part" != "null" ] && [ -n "$bios_start_part" ]; }; then # для export_img_bios_and_uefi_gpt
    ROOT_AT_2=y
elif { [ "$bios_start_part" != "null" ] && [ -n "$bios_start_part" ]; } \
|| { [ "$efi_start_part" != "null" ] && [ -n "$efi_start_part" ]; }; then # для export_img_bios_gpt и export_img_uefi_gpt
    ROOT_AT_1=y
fi

if [ -n "$ROOT_AT_1" ]; then # для export_img_bios_gpt и export_img_uefi_gpt
    image_rootfs_start=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[1].start')
    image_rootfs_size=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[1].size')

    boot_dev=""

    echo "root position: ROOT_AT_1"
elif [ -n "$ROOT_AT_2" ]; then # для export_img_bios_and_uefi_gpt
    image_rootfs_start=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[2].start')
    image_rootfs_size=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[2].size')

    boot_dev=""

    echo "root position: ROOT_AT_2"
elif [ -n "$boot_dev" ] && [ -n "$rootfs_dev" ]; then # rootfs и boot (EFI раздел не считается, только для одноплатников)
    image_boot_start=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[0].start')
    image_boot_size=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[0].size')

    image_rootfs_start=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[1].start')
    image_rootfs_size=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[1].size')

    echo "root position: BOOT-0 and rootfs-1"
elif [ -n "$rootfs_dev" ]; then # когда есть только rootfs. то есть export_img_bios_mbr
    image_rootfs_start=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[0].start')
    image_rootfs_size=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[0].size')

    echo "root position: rootfs-0"
fi

echo "partitiontable: $partitiontable"
echo "sector_size: $sector_size"
echo "image_boot_start: $image_boot_start"
echo "image_boot_size: $image_boot_size"
echo "image_rootfs_start: $image_rootfs_start"
echo "image_rootfs_size: $image_rootfs_size"
echo "result boot device: $boot_dev"

# ------------- get real partitions info

if [ -n "$boot_dev" ]; then
    boot_size=$(blockdev --getsize "$boot_dev")
    echo "boot_size: $boot_size"
fi

if [ -n "$rootfs_dev" ]; then
    rootfs_size=$(blockdev --getsize "$rootfs_dev")
    echo "rootfs_size: $rootfs_size"
fi

# ------------- check partitions size

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

# ------------- check available image partitions

if [ -n "$boot_dev" ] && [ -z "$image_boot_start" ]; then
    echo there are no BOOT partition in the image
    exit 1
fi

if [ -n "$rootfs_dev" ] && [ -z "$image_rootfs_start" ]; then
    echo there are no rootfs partition in the image
    exit 1
fi

# ------------- flash new partitions

BS=4M

if [ -n "$boot_dev" ]; then
    echo "start writing BOOT partition..."

    skip_bytes=$(( image_boot_start * sector_size ))
    count_bytes=$(( image_boot_size * sector_size ))
    /nativedd if="$image_path" of="$boot_dev" bs=$BS skip=$skip_bytes count=$count_bytes status=progress conv=fsync iflag=skip_bytes,count_bytes
fi

if [ -n "$rootfs_dev" ]; then
    echo "start writing rootfs partition..."

    skip_bytes=$(( image_rootfs_start * sector_size ))
    count_bytes=$(( image_rootfs_size * sector_size ))
    /nativedd if="$image_path" of="$rootfs_dev" bs=$BS skip=$skip_bytes count=$count_bytes status=progress conv=fsync iflag=skip_bytes,count_bytes
fi

# -------------

echo "UPDATE DONE!"
