# uwe5622 patches from Armbian for NixOS

## Usage

```nix
inputs.uwe5622-nixos.url = "github:misuzu/uwe5622-nixos";

nixpkgs.overlays = [ inputs.uwe5622-nixos.overlays.default ];

boot.kernelPackages = pkgs.linuxPackages_6_12_uwe5622_sunxi;
boot.kernelModules = [ "sprdwl_ng" "sprdbt_tty" ];
hardware.firmware = [ pkgs.uwe5622-firmware ];
```

## Does this actually work?

The driver is a mess. It can connect to an AP, which is better than nothing I guess.
After that you'll get this:
```
[   29.674766] memcpy: detected field-spanning write (size 16) of single field "vif->key[pairwise][key_index]" at drivers/net/wireless/uwe5622/unisocwifi/cfg80211.c:714 (size 0)
[   29.690909] WARNING: CPU: 3 PID: 718 at drivers/net/wireless/uwe5622/unisocwifi/cfg80211.c:714 sprdwl_cfg80211_add_key+0x180/0x190 [sprdwl_ng]
[   29.704151] Modules linked in: motorcomm crct10dif_ce dwmac_sun8i polyval_ce polyval_generic stmmac_platform stmmac sm4 sunxi_wdt pcs_xpcs sun8i_ce cmdlinepart crypto_engine sun6i_dma xt_conntrack nf_conntrack nf_defrag_ipv6 nf_defrag_ipv4 ip6t_rpfilter ipt_rpfilter xt_pkttype ip6t_REJECT nf_reject_ipv6 ipt_REJECT n
f_reject_ipv4 xt_tcpudp nft_compat nf_tables libcrc32c tcp_bbr sch_fq tap macvlan bridge uio_pdrv_genirq stp uio llc sprdbt_tty sprdwl_ng uwe5622_bsp_sdio cfg80211 rfkill fuse nfnetlink lz4 zram 842_decompress 842_compress lz4hc_compress lz4_compress ip_tables x_tables mmc_block rpmb_core dm_mod dax
[   29.758602] CPU: 3 UID: 0 PID: 718 Comm: wpa_supplicant Not tainted 6.12.23 #1-NixOS
[   29.766464] Hardware name: OrangePi Zero3 (DT)
[   29.771015] pstate: 60000005 (nZCv daif -PAN -UAO -TCO -DIT -SSBS BTYPE=--)
[   29.778046] pc : sprdwl_cfg80211_add_key+0x180/0x190 [sprdwl_ng]
[   29.784460] lr : sprdwl_cfg80211_add_key+0x180/0x190 [sprdwl_ng]
[   29.790847] sp : ffff8000853d3730
[   29.794201] x29: ffff8000853d3730 x28: ffff0000c5679340 x27: ffff0000c5679340
[   29.801410] x26: 0000000000000000 x25: 0000000000000010 x24: 0000000000000000
[   29.808603] x23: ffff0000c299e000 x22: ffff0000c299ea00 x21: 0000000000000004
[   29.815778] x20: ffff0000c299f33c x19: ffff8000853d3780 x18: 0000000000000000
[   29.822949] x17: 0000000000000000 x16: 0000000000000000 x15: 0720072007200720
[   29.830160] x14: 0720072007200720 x13: 0000000000000000 x12: 0000000000000000
[   29.837367] x11: 0000000000000000 x10: 0000000000000000 x9 : 0000000000000000
[   29.844561] x8 : 0000000000000000 x7 : 0000000000000000 x6 : 0000000000000000
[   29.851761] x5 : 0000000000000000 x4 : 0000000000000000 x3 : 0000000000000000
[   29.858942] x2 : 0000000000000000 x1 : 0000000000000000 x0 : 0000000000000000
[   29.866118] Call trace:
[   29.868586]  sprdwl_cfg80211_add_key+0x180/0x190 [sprdwl_ng]
[   29.874596]  nl80211_new_key+0x14c/0x358 [cfg80211]
[   29.880534]  genl_family_rcv_msg_doit+0xe0/0x180
[   29.885270]  genl_rcv_msg+0x250/0x2d8
[   29.888996]  netlink_rcv_skb+0x68/0x160
[   29.892878]  genl_rcv+0x40/0x70
[   29.896045]  netlink_unicast+0x31c/0x380
[   29.899987]  netlink_sendmsg+0x1ac/0x440
[   29.903925]  __sock_sendmsg+0x78/0xf8
[   29.907601]  ____sys_sendmsg+0x290/0x328
[   29.911570]  ___sys_sendmsg+0xb8/0x138
[   29.915362]  __sys_sendmsg+0x90/0x118
[   29.919092]  __arm64_sys_sendmsg+0x2c/0x58
[   29.923244]  invoke_syscall+0x50/0x160
[   29.927047]  el0_svc_common.constprop.0+0x48/0x130
[   29.931885]  do_el0_svc+0x24/0x50
[   29.935248]  el0_svc+0x38/0x140
[   29.938449]  el0t_64_sync_handler+0x140/0x150
[   29.942841]  el0t_64_sync+0x190/0x198
[   29.946523] ---[ end trace 0000000000000000 ]---
```

I've only tested this on my OrangePi Zero3.
