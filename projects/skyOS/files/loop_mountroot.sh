#!/bin/sh

CMDLINE=$(cat /proc/cmdline)
for param in $CMDLINE; do
    case "$param" in
        loop=*)
            LOOP="${param#loop=}"
            ;;
        root_processing)
            ROOT_PROCESSING=y
            ;;
    esac
done

if [ -n "$LOOP" ]; then
    mountroot()
    {
        if [ -n "$ROOT" ]; then
            # local_device_setup "${ROOT}" "root file system"

            if [ "$BOOT" = "nfs" ]; then
                nfs_mount_root
            else
                local_mount_root
            fi

            mkdir -m 0700 /realroot
            mount -n -o move ${rootmnt} /realroot
        fi

        mount -o loop "$LOOP" ${rootmnt}

        if [ -d "/realroot" ]; then
            mount -n -o move /realroot ${rootmnt}/realroot
        fi
    }
fi
