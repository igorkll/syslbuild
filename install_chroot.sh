#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

CHROOT_PATH="/opt/syslbuild_chroot"

echo "INSTALLER: make chroot env: $CHROOT_PATH"

rm -rf "$CHROOT_PATH"
mkdir -p "$CHROOT_PATH"

mmdebstrap --variant=minbase \
  --aptopt='Acquire::Check-Valid-Until "false";' \
  --aptopt='Acquire::AllowInsecureRepositories "true";' \
  --aptopt='APT::Get::AllowUnauthenticated "true";' \
  bookworm \
  "$CHROOT_PATH" \
  https://snapshot.debian.org/archive/debian/20260716T082409Z/

./active_chroot.sh
chroot "$CHROOT_PATH" /opt/install_dependencies.sh
./deactive_chroot.sh
