#!/bin/bash
set -e

if [ -x "/.user_chroot" ]; then
    if [ -f "/.user_chroot_bash" ]; then
        bash /.user_chroot
    else
        /.user_chroot
    fi
    
    rm -f /.user_chroot
    rm -f /.user_chroot_bash
fi

touch /.chrootend
