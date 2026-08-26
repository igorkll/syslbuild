#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

if [ "$PWD" = "/opt/syslbuild" ]; then
  cd ..
  echo "UNINSTALLER: cd $(pwd)"
fi

echo "UNINSTALLER: delete syslbuild"
rm -rf "/opt/syslbuild"

echo "UNINSTALLER: delete system cli tools"
rm -f "/usr/bin/syslbuild"
rm -f "/usr/bin/mkbootable"

echo "UNINSTALLER: delete desktop shortcuts"
rm -f "/usr/share/applications/syslbuild.desktop"
rm -f "/usr/share/applications/gnuboxmaker.desktop"
rm -f "/usr/share/applications/mkbootable.desktop"

echo "UNINSTALLER: update-desktop-database"
update-desktop-database

./uninstall_chroot.sh
