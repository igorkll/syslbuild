#!/bin/bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
mkdir -p $XDG_RUNTIME_DIR
chmod 700 $XDG_RUNTIME_DIR

# ------------- run compositor

start_xserver() {
    local display="$1"
    local xserver_cmd="${2:-X}"

    echo "Starting X-server on display $display..."
    $xserver_cmd "$display" &
    local xpid=$!

    export DISPLAY="$display"

    local sock="/tmp/.X11-unix/X${display#:}"
    until [ -S "$sock" ]; do
        sleep 0.1
    done

    until xdpyinfo >/dev/null 2>&1; do
        sleep 0.1
    done

    echo "X-server on $display is ready (PID $xpid)"
}

KWIN_FLAGS="--no-lockscreen --no-global-shortcuts"

if true; then
    start_xserver ":1"
    
    echo Launching kwin_x11 with flags: $KWIN_FLAGS
    kwin_x11 $KWIN_FLAGS &
else
    if command -v XWayland >/dev/null 2>&1; then
        KWIN_FLAGS="$KWIN_FLAGS --xwayland"
    fi

    echo Launching kwin_wayland with flags: $KWIN_FLAGS
    kwin_wayland $KWIN_FLAGS &
fi

# ------------- run shell
plymouth quit
sleep 3

electron --ozone-platform=wayland --enable-features=UseOzonePlatform,WaylandWindowDecorations --no-sandbox /sky/system/ElectronApplication
bash