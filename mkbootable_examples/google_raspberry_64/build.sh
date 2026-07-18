#!/bin/bash

# --x11-session is optional, without it, the wayland session will simply be used

mkbootable --x11-session --platform raspberry_pi_64 --web https://google.com --output kiosk_google_rpi_64.img
