#!/bin/sh

PREREQ=""

prereqs() {
    echo "$PREREQ"
}

case "$1" in
    prereqs)
        prereqs
        exit 0
        ;;
esac

. /usr/share/initramfs-tools/hook-functions

if [ -e "/startup.wav" ]; then
    cp /startup.wav "${DESTDIR}/startup.wav"
fi

copy_exec /usr/bin/bash /usr/bin
copy_exec /usr/bin/findmnt /usr/bin
copy_exec /usr/bin/jq /usr/bin
copy_exec /usr/sbin/blockdev /usr/sbin
copy_exec /usr/bin/dd /nativedd
copy_exec /usr/bin/umount /nativeumount
