#!/bin/bash

stty -echo >/dev/null 2>&1

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec weston --continue-without-input --renderer=pixman >/dev/null 2>&1
else
    reset
    exec bash
fi
