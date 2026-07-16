#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

CHROOT_PATH="/opt/syslbuild_chroot"

./deactive_chroot.sh "$CHROOT_PATH"
rm -rf "$CHROOT_PATH"
