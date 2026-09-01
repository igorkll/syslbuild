#!/bin/bash

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    stty -echo >/dev/null 2>&1
    setterm -cursor off
    clear

    if [ -e "/bootmnt/rpi_64" ]; then
        exec weston --continue-without-input --renderer=pixman >/dev/null 2>&1
    else
        exec weston --continue-without-input >/dev/null 2>&1
    fi
else
    reset
    exec bash
fi
