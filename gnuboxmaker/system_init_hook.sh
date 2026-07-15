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

copy_exec /usr/bin/bash /usr/bin
copy_exec /usr/bin/findmnt /usr/bin
copy_exec /usr/bin/jq /usr/bin
copy_exec /usr/sbin/blockdev /usr/sbin
copy_exec /usr/bin/dd /nativedd
copy_exec /usr/bin/umount /nativeumount

if [ -e "/startup.wav" ]; then
    cp /startup.wav "${DESTDIR}/startup.wav"

    for mod in $(find /lib/modules/$(cat /.kernel_version)/kernel -name "snd*.ko" -exec basename {} .ko \; | sort -u); do
        manual_add_modules "$mod"
    done
fi

if [ -d "/user_initramfs" ]; then
    cp -a /user_initramfs/. "${DESTDIR}"
fi
