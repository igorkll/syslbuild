#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

CHROOT_PATH="/opt/syslbuild_chroot"

mkdir -p "$CHROOT_PATH/opt/syslbuild"

mount --bind /opt/syslbuild "$CHROOT_PATH/opt/syslbuild"
mount -t proc /proc "$CHROOT_PATH/proc"
mount --bind /dev "$CHROOT_PATH/dev"
mount --bind /sys "$CHROOT_PATH/sys"


