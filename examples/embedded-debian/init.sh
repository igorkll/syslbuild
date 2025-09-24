#!/bin/bash
sleep 3
plymouth quit

mkdir -p /dev/shm
mount -t tmpfs -o rw,nosuid,nodev,noexec,relatime,size=64M tmpfs /dev/shm
chmod 1700 /dev/shm

xinit /usr/local/bin/electron /embedded/ElectronApplication -- :0