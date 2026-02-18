#!/bin/bash

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    # disable tty hotkeys
    stty intr undef   # Ctrl+C
    stty quit undef   # Ctrl+\\
    stty stop undef   # Ctrl+S
    stty start undef  # Ctrl+Q
    stty susp undef   # Ctrl+Z

    # disable echo mode
    stty -echo

    # clear screen and set cursor to first line
    touch /tmp/plymouth_quit
    clear

    exec weston --continue-without-input --renderer=pixman >/dev/null 2>&1
else
    exec bash
fi
