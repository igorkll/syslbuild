#!/bin/bash

if command -v plymouth >/dev/null 2>&1; then
    plymouth quit --wait # suid binary in gnubox maker
fi

exec weston --continue-without-input --renderer=pixman >/dev/null 2>&1
