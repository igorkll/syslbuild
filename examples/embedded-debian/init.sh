#!/bin/bash
plymouth quit
Xorg :0 &
export DISPLAY=:0
electron /embedded/ElectronApplication