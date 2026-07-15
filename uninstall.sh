#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

cd ..

echo "INSTALLER: delete syslbuild"
rm -rf "/opt/syslbuild"

echo "INSTALLER: delete system cli tools"
rm -f "/usr/bin/syslbuild"
rm -f "/usr/bin/mkbootable"

echo "INSTALLER: delete desktop shortcuts"
rm -f "/usr/share/applications/syslbuild.desktop"
rm -f "/usr/share/applications/gnuboxmaker.desktop"
rm -f "/usr/share/applications/mkbootable.desktop"

echo "INSTALLER: update-desktop-database"
update-desktop-database
