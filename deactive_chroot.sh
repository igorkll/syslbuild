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

echo "deactive chroot: $CHROOT_PATH"

umount "$CHROOT_PATH/sys/fs/cgroup"
umount "$CHROOT_PATH/sys/fs/cgroup"
umount "$CHROOT_PATH/sys"
umount "$CHROOT_PATH/proc"
umount "$CHROOT_PATH/run"
umount "$CHROOT_PATH/dev"
umount -l "$CHROOT_PATH/opt/syslbuild"
