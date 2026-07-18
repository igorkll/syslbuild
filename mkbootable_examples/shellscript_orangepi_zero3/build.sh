#!/bin/bash

mkbootable --platform orange_pi_zero3 --application shellscript.sh --packages lua5.3,python3,w3m,dialog,fdisk --root-privileges --output shellscript_orangepi_zero3.img
