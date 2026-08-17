#!/bin/bash

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    stty -echo >/dev/null 2>&1
    clear

    /gnubox/run_session_wayland_raw.sh
else
    clear
    reset
    exec bash
fi
