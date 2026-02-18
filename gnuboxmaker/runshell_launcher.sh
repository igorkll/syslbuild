#!/bin/bash

while true; do
    # disable tty hotkeys
    stty intr undef >/dev/null 2>&1  # Ctrl+C
    stty quit undef >/dev/null 2>&1  # Ctrl+\\
    stty stop undef >/dev/null 2>&1  # Ctrl+S
    stty start undef >/dev/null 2>&1 # Ctrl+Q
    stty susp undef >/dev/null 2>&1  # Ctrl+Z

    # disable echo mode
    stty -echo >/dev/null 2>&1

    # clear screen and set cursor to first line
    clear

    # run user application
    /runshell.sh
done
