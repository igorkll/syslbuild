#!/bin/bash

wpctl set-volume @DEFAULT_SINK@ 1

while true; do
    aplay /output.wav
    sleep 1
done
