#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

echo "INSTALLER: apt update"
apt update

echo "INSTALLER: install system packages"
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
apt install -y 7zip 7zip-rar
apt install -y patch
apt install -y bc bison flex libssl-dev libelf-dev
apt install -y rsync cpio initramfs-tools diffutils

echo "INSTALLER: install python packages"
pip install json5 --break-system-packages
pip install asteval --break-system-packages
pip install favicon --break-system-packages
pip install requests --break-system-packages
pip install Pillow --break-system-packages
