#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

PROJECT_PATH="$1"
CHROOT_PATH="/opt/syslbuild_chroot"

PROJECT_NAME="${PROJECT_PATH##*/}"

mkdir -p "$CHROOT_PATH/project"
mount --bind "$PROJECT_PATH" "$CHROOT_PATH/project"

shift

cat > "$CHROOT_PATH/build.sh" <<EOF
#!/bin/bash

cd project
/opt/syslbuild/syslbuild.py "$PROJECT_NAME" --disable-chroot "$@"

EOF

./active_chroot.sh "$CHROOT_PATH"
chroot "$CHROOT_PATH" /build.sh
./deactive_chroot.sh "$CHROOT_PATH"

umount "$CHROOT_PATH/project"
