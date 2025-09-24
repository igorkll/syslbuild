#!/bin/bash
Xorg :0 vt1 -nolisten tcp &
sleep 3
plymouth quit
export DISPLAY=:0
/usr/local/bin/electron --no-sandbox /embedded/ElectronApplication
