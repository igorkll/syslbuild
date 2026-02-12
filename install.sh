#!/bin/sh

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

