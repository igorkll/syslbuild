#!/bin/sh

CMDLINE=$(cat /proc/cmdline)
for param in $CMDLINE; do
    case "$param" in
        loop=*)
            LOOP="${param#loop=}"
            ;;
    esac
done

if [ -n "$LOOP" ]; then
    mountroot()
    {
        if [ -n "$ROOT" ]; then
            if [ "$BOOT" = "nfs" ]; then
                nfs_mount_root
            else
                local_mount_root
            fi

            mkdir -m 0700 /realroot
            mount -n -o move ${rootmnt} /realroot
        fi

        mount -n -o move /root ${rootmnt}/run
    }
fi
