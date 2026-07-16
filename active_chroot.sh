#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

CHROOT_PATH=""
DISABLE_AUTOMOUNTS=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --disable-automounts)
            DISABLE_AUTOMOUNTS=1
            shift
            ;;
        *)
            if [ -z "$CHROOT_PATH" ]; then
                CHROOT_PATH="$1"
                shift
            else
                echo "Error: unexpected argument '$1'"
                exit 1
            fi
            ;;
    esac
done

if [ -z "$CHROOT_PATH" ]; then
    echo "Error: no chroot path specified."
    echo "Usage: $0 <chroot_path>"
    exit 1
fi

if [ ! -d "$CHROOT_PATH" ]; then
    echo "Error: '$CHROOT_PATH' is not an existing directory."
    exit 1
fi

/opt/syslbuild/deactive_chroot.sh "$CHROOT_PATH"

echo "active chroot: $CHROOT_PATH"

mkdir -p "$CHROOT_PATH/opt/syslbuild"
mount --bind /opt/syslbuild "$CHROOT_PATH/opt/syslbuild"

if [ "$DISABLE_AUTOMOUNTS" -eq 0 ]; then
    mount --bind /dev "$CHROOT_PATH/dev"
    mount --bind /run "$CHROOT_PATH/run"
    mount -t proc /proc "$CHROOT_PATH/proc"
    mount -t sysfs sys "$CHROOT_PATH/sys"
else
    echo "Skipping automounts"
fi
