#!/bin/bash

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    stty -echo >/dev/null 2>&1
    setterm -cursor off
    clear
    
    if [ -x "/gnubox/custom_x11_run.sh" ]; then
        exec /gnubox/custom_x11_run.sh
    else
        startx > /dev/null 2>&1
    fi
else
    clear
    reset
    exec -l bash
fi
