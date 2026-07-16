#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

CHROOT_PATH="$1"

if [ -z "$CHROOT_PATH" ]; then
    echo "Error: no chroot path specified."
    echo "Usage: $0 <chroot_path>"
    exit 1
fi

if [ ! -d "$CHROOT_PATH" ]; then
    echo "Error: '$CHROOT_PATH' is not an existing directory."
    exit 1
fi

/opt/syslbuild/deactive_chroot.sh "$CHROOT_PATH"

echo "active chroot: $CHROOT_PATH"

mkdir -p "$CHROOT_PATH/opt/syslbuild"

mount --bind /opt/syslbuild "$CHROOT_PATH/opt/syslbuild"

mount --bind /dev "$CHROOT_PATH/dev"
mount --bind /run "$CHROOT_PATH/run"

mount -t proc /proc "$CHROOT_PATH/proc"
mount -t sysfs sys "$CHROOT_PATH/sys"
mount -t tmpfs tmpfs "$CHROOT_PATH/sys/fs/cgroup"
mount -t cgroup2 cgroup2 "$CHROOT_PATH/sys/fs/cgroup"


