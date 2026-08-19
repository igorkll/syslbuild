#!/bin/bash

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    stty -echo >/dev/null 2>&1
    setterm -cursor off
    clear
    
    startx > /dev/null 2>&1
else
    exec bash
fi
