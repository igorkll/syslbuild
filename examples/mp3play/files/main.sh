#!/bin/bash

export HOME=/root

export XDG_RUNTIME_DIR=/run/user/0
mkdir -p $XDG_RUNTIME_DIR
chmod 700 $XDG_RUNTIME_DIR

pulseaudio --start --exit-idle-time=-1

while true; do
    mpg123 -o pulse /sound.mp3
    sleep 1
done