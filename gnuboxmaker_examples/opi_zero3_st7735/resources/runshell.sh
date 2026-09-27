#!/bin/bash

electron /ElectronApplication --disable-gpu-vsync --disable-frame-rate-limit --enable-gpu-rasterization --ignore-gpu-blocklist --ozone-platform=wayland --enable-features=UseOzonePlatform --no-sandbox
