#!/bin/bash

if [ -e "/bootmnt/opi_zero3" ] || [ -e "/bootmnt/rpi_64" ]; then
    exec weston --continue-without-input --renderer=pixman >/dev/null 2>&1
else
    exec weston --continue-without-input >/dev/null 2>&1
fi
