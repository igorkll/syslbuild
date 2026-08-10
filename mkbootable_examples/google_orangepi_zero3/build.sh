#!/bin/bash

# --x11-session is optional, without it, the wayland session will simply be used

mkbootable --x11-session --platform orange_pi_zero3 --web https://google.com --output kiosk_google_opi_zero3.img
