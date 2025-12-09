run_in_chroot() {
    local CHROOT_PATH="$1"
    local SCRIPT_PATH="$2"

    cp "$SCRIPT_PATH" "$CHROOT_PATH/.build_script" || return 1
    chmod +x "$CHROOT_PATH/.build_script" || return 1
    chroot "$CHROOT_PATH" /bin/bash /.build_script || return 1
    rm -f "$CHROOT_PATH/.build_script"
}

run_in_chroot "$1" hooks/chroot/dependencies.sh
run_in_chroot "$1" hooks/chroot/boot_logo.sh
