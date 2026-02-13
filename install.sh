#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

sudo apt install -y \
  python3 wget sudo git make tar gzip \
  coreutils util-linux mount \
  ncurses-bin systemd-container
sudo apt install -y \
  e2fsprogs dosfstools btrfs-progs xfsprogs
sudo apt install -y \
  mmdebstrap qemu-user-static binfmt-support
sudo apt install -y \
  grub-pc-bin grub-efi-amd64-bin grub-common \
  xorriso
sudo apt install -y \
  gcc-x86-64-linux-gnu \
  gcc-i686-linux-gnu \
  gcc-aarch64-linux-gnu \
  gcc-arm-linux-gnueabihf \
  gcc-arm-linux-gnueabi
sudo apt install -y u-boot-tools
sudo apt install -y arch-install-scripts
sudo apt install -y grub-efi-ia32-bin grub-common
sudo pip install json5 --break-system-packages
sudo pip install asteval --break-system-packages

DEST="/opt/syslbuild"
sudo mkdir -p "$DEST"
sudo cp -r ./* "$DEST"
sudo chmod -R 755 "$DEST"

sudo cp -f "syslbuild.py" "/usr/bin/syslbuild"
sudo cp -f "syslbuild.desktop" "/usr/share/applications/syslbuild.desktop"
sudo cp -f "gnuboxmaker.desktop" "/usr/share/applications/gnuboxmaker.desktop"

sudo chmod 755 "/usr/bin/syslbuild"
sudo chmod 755 "/usr/share/applications/syslbuild.desktop"
sudo chmod 755 "/usr/share/applications/gnuboxmaker.desktop"

sudo update-desktop-database