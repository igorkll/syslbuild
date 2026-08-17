#!/bin/bash

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    export XDG_RUNTIME_DIR=/run/user/$(id -u)
    export XDG_CURRENT_DESKTOP=weston
    systemctl --user start gnubox_weston.service
    wait
else
    clear
    reset
    exec bash
fi
