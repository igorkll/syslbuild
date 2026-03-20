#!/bin/bash

electron /ElectronApplication --enable-gpu-rasterization --ignore-gpu-blocklist --ozone-platform=wayland --enable-features=UseOzonePlatform --no-sandbox
