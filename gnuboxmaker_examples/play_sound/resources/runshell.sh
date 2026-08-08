#!/bin/bash

amixer sset Master 100%

while true; do
    aplay /output.wav
    sleep 1
done
