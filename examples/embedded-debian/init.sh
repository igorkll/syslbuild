#!/bin/bash
plymouth quit
Xorg :0 vt1 -nolisten tcp &
export DISPLAY=:0
/usr/local/bin/electron --no-sandbox /embedded/ElectronApplication
