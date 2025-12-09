#!/bin/bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
mkdir -p $XDG_RUNTIME_DIR
chmod 700 $XDG_RUNTIME_DIR
dbus-launch --exit-with-session &

weston --tty=1 --no-config &
export WAYLAND_DISPLAY=wayland-0

/usr/local/bin/electron --no-sandbox /embedded/ElectronApplication
bash

killall weston
