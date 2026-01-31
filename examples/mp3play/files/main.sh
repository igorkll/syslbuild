#!/bin/bash

export HOME=/root

export XDG_RUNTIME_DIR=/run/user/0
mkdir -p $XDG_RUNTIME_DIR
chmod 700 $XDG_RUNTIME_DIR

mount -t tmpfs -o "nodev,nosuid,size=${RUNSIZE:-10%},mode=1777" tmpfs /var
mount -t tmpfs -o "nodev,nosuid,size=${RUNSIZE:-10%},mode=1777" tmpfs /root

pulseaudio --daemonize=yes --exit-idle-time=-1

bash

while true; do
    mpg123 -o pulse /sound.mp3
    sleep 1
done