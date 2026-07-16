#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

CHROOT_PATH="/opt/syslbuild_chroot"

PROJECT_PATH="$1"
PROJECT_DIR="$(dirname "$PROJECT_PATH")"
PROJECT_NAME="$(basename "$PROJECT_PATH")"

mkdir -p "$CHROOT_PATH/project"
mount --bind "$PROJECT_DIR" "$CHROOT_PATH/project"

shift
args=()
for arg in "$@"; do
    args+=("$(printf "%q" "$arg")")
done

cat > "$CHROOT_PATH/build.sh" <<EOF
#!/bin/bash

cd /project
/opt/syslbuild/syslbuild.py "$PROJECT_NAME" --disable-chroot ${args[*]}

EOF

./active_chroot.sh "$CHROOT_PATH"
chmod +x "$CHROOT_PATH/build.sh"
chroot "$CHROOT_PATH" /build.sh
./deactive_chroot.sh "$CHROOT_PATH"

umount "$CHROOT_PATH/project"
