#!/bin/bash

systemctl --user enable pipewire pipewire-pulse wireplumber
systemctl --user start pipewire pipewire-pulse wireplumber

electron /ElectronApplication --enable-gpu-rasterization --ignore-gpu-blocklist --no-sandbox
