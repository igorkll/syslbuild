#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

./uninstall.sh
./install_dependencies.sh

echo "INSTALLER: copy syslbuild files"
DEST="/opt/syslbuild"
mkdir -p "$DEST"
cp -r ./* "$DEST"
chmod -R 755 "$DEST"

echo "INSTALLER: install system cli tools"
cp -f "syslbuild.py" "/usr/bin/syslbuild"
cp -f "mkbootable.py" "/usr/bin/mkbootable"
chmod 755 "/usr/bin/syslbuild"
chmod 755 "/usr/bin/mkbootable"

echo "INSTALLER: make desktop shortcuts"
cp -f "syslbuild.desktop" "/usr/share/applications/syslbuild.desktop"
cp -f "gnuboxmaker.desktop" "/usr/share/applications/gnuboxmaker.desktop"
cp -f "mkbootable.desktop" "/usr/share/applications/mkbootable.desktop"
chmod 755 "/usr/share/applications/syslbuild.desktop"
chmod 755 "/usr/share/applications/gnuboxmaker.desktop"
chmod 755 "/usr/share/applications/mkbootable.desktop"

echo "INSTALLER: prepair installed syslbuild"
cd "$DEST"
./prepair.sh

echo "INSTALLER: update-desktop-database"
update-desktop-database

./install_chroot.sh
