#!/bin/bash

stty -echo >/dev/null 2>&1

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    startx > /dev/null 2>&1
else
    reset
    exec bash
fi
