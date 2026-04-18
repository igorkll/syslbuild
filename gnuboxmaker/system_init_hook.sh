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
