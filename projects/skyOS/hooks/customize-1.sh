run_in_chroot() {
    local CHROOT_PATH="$1"
    local SCRIPT_PATH="$2"

    cp "$SCRIPT_PATH" "$CHROOT_PATH/.build_script" || return 1
    chmod +x "$CHROOT_PATH/.build_script" || return 1
    chroot "$CHROOT_PATH" /bin/bash /.build_script || return 1
    rm -f "$CHROOT_PATH/.build_script"
}

# ----------------- copy files
install -Dm644 files/skystart.service "$1/etc/systemd/system/skystart.service"
install -Dm755 files/custom_init.sh "$1/usr/share/initramfs-tools/init"

# ----------------- chroot scripts
run_in_chroot "$1" hooks/chroot/apply_settings.sh
run_in_chroot "$1" hooks/chroot/dependencies.sh
run_in_chroot "$1" hooks/chroot/boot_logo.sh
run_in_chroot "$1" hooks/chroot/disable_trash.sh
run_in_chroot "$1" hooks/chroot/register_skystart.sh
run_in_chroot "$1" hooks/chroot/make_initramfs.sh
# run_in_chroot "$1" hooks/chroot/cleanup.sh
