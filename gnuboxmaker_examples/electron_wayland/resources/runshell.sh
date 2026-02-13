#!/bin/bash

weston-terminal

electron /ElectronApplication --ozone-platform=wayland --enable-features=UseOzonePlatform --no-sandbox
