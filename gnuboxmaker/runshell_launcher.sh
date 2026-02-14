#!/bin/bash

while true; do
    # disable tty hotkeys
    stty intr undef   # Ctrl+C
    stty quit undef   # Ctrl+\\
    stty stop undef   # Ctrl+S
    stty start undef  # Ctrl+Q
    stty susp undef   # Ctrl+Z

    # disable echo mode
    stty -echo

    # clear screen and set cursor to first line
    clear

    # run user application
    /runshell.sh
done
