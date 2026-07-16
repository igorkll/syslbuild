#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

CHROOT_PATH="/opt/syslbuild_chroot"

echo "deactive chroot: $CHROOT_PATH"

umount "$CHROOT_PATH/opt/syslbuild"
umount "$CHROOT_PATH/proc"
umount "$CHROOT_PATH/dev"
umount "$CHROOT_PATH/sys"
