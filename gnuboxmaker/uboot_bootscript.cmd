setenv bootm_size 0x20000000
setenv initrd_high 0xffffffff
setenv fdt_high 0xffffffff
run boot_extlinux
