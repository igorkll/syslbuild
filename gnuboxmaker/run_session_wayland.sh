#!/bin/bash

if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec weston >/dev/null 2>&1
else
    exec bash
fi
