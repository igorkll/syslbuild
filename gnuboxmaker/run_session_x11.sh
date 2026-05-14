#!/bin/bash

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    stty -echo >/dev/null 2>&1
    clear
    
    startx > /dev/null 2>&1
else
    reset
    clear
    exec bash
fi
