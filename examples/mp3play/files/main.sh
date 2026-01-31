#!/bin/bash

pulseaudio --start --exit-idle-time=-1

while true; do
    mpg123 -o pulse /sound.mp3
    sleep 1
done