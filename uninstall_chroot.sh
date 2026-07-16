#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

CHROOT_PATH="/opt/syslbuild_chroot"

umount "$CHROOT_PATH/sys"
umount "$CHROOT_PATH/proc"
umount "$CHROOT_PATH/dev"

rm -rf "$CHROOT_PATH"
