#!/bin/bash

echo "uninitialized" > /etc/machine-id

apt autoremove -y
apt clean

rm -rf /var/lib/apt/lists/*
rm -rf /var/cache/apt/*.bin
rm -rf /var/log/apt/*.log
rm -rf /var/cache/debconf/*
