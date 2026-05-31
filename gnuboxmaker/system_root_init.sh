#!/bin/sh

if [ -e "/bootmnt/opi_zero3" ]; then
    modprobe /lib/modules/kernel/drivers/net/wireless/uwe5622/unisocwifi/sprdwl_ng.ko
fi
