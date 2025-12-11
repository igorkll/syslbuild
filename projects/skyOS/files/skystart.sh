#!/bin/bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
mkdir -p $XDG_RUNTIME_DIR
chmod 700 $XDG_RUNTIME_DIR

# ------------- drivers
modprobe nvidia-drm modeset=1

# ------------- run compositor
KWIN_FLAGS="--no-lockscreen --no-global-shortcuts"
if command -v XWayland >/dev/null 2>&1; then
    KWIN_FLAGS="$KWIN_FLAGS --xwayland"
fi
kwin_wayland $KWIN_FLAGS &

# ------------- run shell
electron --ozone-platform=wayland --enable-features=UseOzonePlatform,WaylandWindowDecorations --no-sandbox /sky/system/ElectronApplication
