#!/bin/bash
set -e

npm install -g --allow-scripts=electron electron@39.2.7
chmod 4755 /usr/local/lib/node_modules/electron/dist/chrome-sandbox

touch /.chrootend