#!/bin/bash

if [ -e "/gnubox/.session_mode_tty" ]; then
    if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
        :
    else
        clear
        reset
        exec bash
    fi
fi

while true; do
    clear

    if [ -e "/gnubox/.enable_echo" ]; then
        stty echo
    else
        stty -echo
    fi

    if [ -e "/gnubox/.enable_cursor" ]; then
        setterm -cursor on
    else
        setterm -cursor off
    fi

    clear

    /gnubox/runshell.sh
    sleep 1
done
