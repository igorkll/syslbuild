run_in_chroot() {
    local CHROOT_PATH="$1"
    local SCRIPT_PATH="$2"

    if [[ -z "$CHROOT_PATH" || -z "$SCRIPT_PATH" ]]; then
        echo "Usage: run_in_chroot <chroot_path> <script_path>"
        return 1
    fi

    cp "$SCRIPT_PATH" "$CHROOT_PATH/.build_script" || return 1
    chmod +x "$CHROOT_PATH/.build_script" || return 1
    chroot "$CHROOT_PATH" /bin/bash /.build_script || return 1
    rm -f "$CHROOT_PATH/.build_script"
}

run_in_chroot "$1" chroot/.sh
