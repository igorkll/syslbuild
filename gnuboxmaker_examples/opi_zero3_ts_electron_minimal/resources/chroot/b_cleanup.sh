#!/bin/bash

# This script won’t work anyway without NodeJS installed. So we’ll remove it, since in this example NodeJS isn’t included in the system.
# use: /usr/local/lib/node_modules/electron/dist/electron
rm -f /usr/local/bin/electron

# We’re still removing npm.
rm -rf /root/.cache
rm -rf /root/.npm

# We don’t need this.
rm -rf /usr/share/doc/*
