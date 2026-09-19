#!/bin/bash

# ------------- copy script to tmp

if [ "${0#/tmp/}" = "$0" ]; then
    echo "Moving self-update script to /tmp"
    cp -p "$0" /tmp/updatescript.sh
    exec /tmp/updatescript.sh "$@"
fi

# ------------- funcstions

for x in $(cat /proc/cmdline); do
	case $x in
	plymouth_show_update_status)
		plymouth_show_update_status=y
		;;
	esac
done

show_status() {
    if [ -n "$plymouth_show_update_status" ]; then
        if command -v plymouth > /dev/null 2>&1; then
            plymouth update --status="$1"
        fi
    fi
    echo "$1"
}

# ------------- mounts

show_status "Starting update..."

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

# проверка типов разделов, чтобы не обновлять те что обновления не требуют
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

if { [ "$efi_start_part" != "null" ] && [ -n "$efi_start_part" ]; } \
&& { [ "$bios_start_part" != "null" ] && [ -n "$bios_start_part" ]; }; then # для export_img_bios_and_uefi_gpt
    ROOT_AT_2=y
elif { [ "$bios_start_part" != "null" ] && [ -n "$bios_start_part" ]; }; then # для export_img_bios_gpt
    ROOT_AT_1=y
fi

if [ -n "$ROOT_AT_1" ]; then # для export_img_bios_gpt
    image_rootfs_start=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[1].start')
    image_rootfs_size=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[1].size')

    boot_dev=""

    echo "root position: ROOT_AT_1"
elif [ -n "$ROOT_AT_2" ]; then # для export_img_bios_and_uefi_gpt
    image_boot_start=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[0].start')
    image_boot_size=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[0].size')

    image_rootfs_start=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[2].start')
    image_rootfs_size=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[2].size')

    echo "root position: ROOT_AT_2"
elif [ -n "$boot_dev" ] && [ -n "$rootfs_dev" ]; then # rootfs и boot / EFI. то есть для одноплатников и export_img_uefi_gpt
    image_boot_start=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[0].start')
    image_boot_size=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[0].size')

    image_rootfs_start=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[1].start')
    image_rootfs_size=$(echo "$partitiontable" | jq -r '.partitiontable.partitions[1].size')

    echo "root position: boot-0 and rootfs-1"
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
        show_status "boot partition in image is bigger than target"
        exit 1
    fi
fi

if [ -n "$image_rootfs_size" ] && [ -n "$rootfs_dev" ]; then
    if [ "$image_rootfs_size" -gt "$rootfs_size" ]; then
        show_status "rootfs partition in image is bigger than target"
        exit 1
    fi
fi

# ------------- check available image partitions

if [ -n "$boot_dev" ] && [ -z "$image_boot_start" ]; then
    show_status "there are no boot partition in the image"
    exit 1
fi

if [ -n "$rootfs_dev" ] && [ -z "$image_rootfs_start" ]; then
    show_status "there are no rootfs partition in the image"
    exit 1
fi

# ------------- flash new partitions

BS=4M
MAX_ATTEMPT=5

part_hash_from_image() {
    local skip_bytes="$1"
    local count_bytes="$2"
    /nativedd if="$image_path" bs=$BS skip=$skip_bytes count=$count_bytes iflag=skip_bytes,count_bytes status=none | sha256sum | /nativeawk '{print $1}'
}

part_hash_from_device() {
    local dev="$1"
    local count_bytes="$2"
    /nativedd if="$dev" bs=$BS count=$count_bytes iflag=count_bytes status=none | sha256sum | /nativeawk '{print $1}'
}

flash_partition() {
    local part="$1"
    local skip_bytes="$2"
    local count_bytes="$3"
    /nativedd if="$image_path" of="$part" bs=$BS skip=$skip_bytes count=$count_bytes status=progress conv=fsync iflag=skip_bytes,count_bytes
}

flash_partition_and_verify() {
    local name="$1"
    local part="$2"
    local skip_bytes="$3"
    local count_bytes="$4"
    
    local attempt=1
    while [ "$attempt" -le "$MAX_ATTEMPT" ]; do
        show_status "writing $name partition (attempt $attempt/$MAX_ATTEMPT)..."
        flash_partition "$boot_dev" "$skip_bytes" "$count_bytes"
        sync
        show_status "verifying $name partition..."



        attempt=$((attempt + 1))
    done

    show_status "failed to write $name partition"
    return 1
}

if [ -n "$boot_dev" ]; then
    skip_bytes=$(( image_boot_start * sector_size ))
    count_bytes=$(( image_boot_size * sector_size ))
    flash_partition_and_verify "boot" "$boot_dev" "$skip_bytes" "$count_bytes" || exit 1
fi

if [ -n "$rootfs_dev" ]; then
    skip_bytes=$(( image_rootfs_start * sector_size ))
    count_bytes=$(( image_rootfs_size * sector_size ))
    flash_partition_and_verify "rootfs" "$boot_dev" "$skip_bytes" "$count_bytes" || exit 1
fi

sync

# -------------

show_status "update done!"
