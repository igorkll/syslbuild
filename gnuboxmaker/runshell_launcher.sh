#!/bin/bash

if [ -e "/gnubox/.session_mode_tty" ]; then
    if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
        # disable echo mode
        stty -echo >/dev/null 2>&1
    else
        reset
        clear
        exec bash
        exit
    fi
fi

while true; do
    /gnubox/runshell.sh
    sleep 1
done
