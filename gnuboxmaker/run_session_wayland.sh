#!/bin/bash

if command -v plymouth >/dev/null 2>&1; then
    plymouth quit --wait # suid binary in gnubox maker
fi

exec weston --backend=drm-backend.so --tty=1 --continue-without-input --renderer=pixman
