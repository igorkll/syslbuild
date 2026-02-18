#!/bin/bash

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    # disable tty hotkeys
    stty intr undef >/dev/null 2>&1  # Ctrl+C
    stty quit undef >/dev/null 2>&1  # Ctrl+\\
    stty stop undef >/dev/null 2>&1  # Ctrl+S
    stty start undef >/dev/null 2>&1 # Ctrl+Q
    stty susp undef >/dev/null 2>&1  # Ctrl+Z

    # disable echo mode
    stty -echo >/dev/null 2>&1

    # plymouth quit
    touch /tmp/plymouth_quit
    sleep 1

    exec weston --continue-without-input --renderer=pixman >/dev/null 2>&1
else
    exec bash
fi
