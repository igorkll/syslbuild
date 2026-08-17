#!/bin/bash

if [ -e "/gnubox/.session_mode_tty" ]; then
    if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    else
        clear
        reset
        clear
        exec bash
    fi
fi

while true; do
    reset
    stty -echo >/dev/null 2>&1
    /gnubox/runshell.sh
    sleep 1
done
