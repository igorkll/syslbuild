#!/bin/bash

bash

export XDG_RUNTIME_DIR=/run/user/$(id -u)
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

pulseaudio --daemonize=yes --exit-idle-time=-1

while true; do
    mpg123 -o pulse /sound.mp3
    sleep 1
done