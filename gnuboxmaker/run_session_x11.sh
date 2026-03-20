#!/bin/bash

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    startx
else
    reset
    exec bash
fi
