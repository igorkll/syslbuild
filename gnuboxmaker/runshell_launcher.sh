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

    if [ -e "/gnubox/.enable_echo" ]; then
        stty echo >/dev/null 2>&1
    else
        stty -echo >/dev/null 2>&1
    fi

    if [ -e "/gnubox/.enable_cursor" ]; then
        setterm -cursor on >/dev/null 2>&1
    else
        setterm -cursor off >/dev/null 2>&1
    fi

    /gnubox/runshell.sh
    sleep 1
done
