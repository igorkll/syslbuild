#!/bin/bash

if [ -e "/gnubox/.session_mode_tty" ]; then
    if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
        :
    else
        exec bash
    fi
fi

while true; do
    clear
    reset
    stty -echo >/dev/null 2>&1
    setterm -cursor off
    clear

    /gnubox/runshell.sh
    sleep 1
done
