#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

apt update

apt install -y \
  python3 wget git make tar gzip \
  coreutils util-linux mount \
  ncurses-bin systemd-container
apt install -y \
  e2fsprogs dosfstools btrfs-progs xfsprogs
apt install -y \
  mmdebstrap qemu-user-static binfmt-support
apt install -y \
  grub-pc-bin grub-efi-amd64-bin grub-common \
  xorriso
apt install -y \
  gcc-x86-64-linux-gnu \
  gcc-i686-linux-gnu \
  gcc-aarch64-linux-gnu \
  gcc-arm-linux-gnueabihf \
  gcc-arm-linux-gnueabi
apt install -y u-boot-tools
apt install -y arch-install-scripts
apt install -y grub-efi-ia32-bin grub-common
apt install -y device-tree-compiler
pip install json5 --break-system-packages
pip install asteval --break-system-packages

./prepair.sh

DEST="/opt/syslbuild"
mkdir -p "$DEST"
cp -r ./* "$DEST"
chmod -R 755 "$DEST"

cp -f "syslbuild.py" "/usr/bin/syslbuild"
cp -f "syslbuild.desktop" "/usr/share/applications/syslbuild.desktop"
cp -f "gnuboxmaker.desktop" "/usr/share/applications/gnuboxmaker.desktop"

chmod 755 "/usr/bin/syslbuild"
chmod 755 "/usr/share/applications/syslbuild.desktop"
chmod 755 "/usr/share/applications/gnuboxmaker.desktop"

update-desktop-database
