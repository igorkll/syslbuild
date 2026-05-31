#!/bin/sh

if [ -e "/bootmnt/opi_zero3" ]; then
    modprobe /lib/modules/6.6.0-rc2-embedded-opi-zero3+/kernel/drivers/net/wireless/uwe5622/unisocwifi/sprdwl_ng.ko
fi
