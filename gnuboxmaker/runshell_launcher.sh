#!/bin/bash

if [ -e "/.session_mode_tty" ]; then
    # disable echo mode
    stty -echo >/dev/null 2>&1
fi

while true; do
    /runshell.sh
    sleep 1
done
