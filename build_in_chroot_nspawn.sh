#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

CHROOT_PATH="/opt/syslbuild_chroot"

PROJECT_PATH="$(realpath "$1")"
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

/opt/syslbuild/active_chroot.sh "$CHROOT_PATH" --disable-automounts
chmod +x "$CHROOT_PATH/build.sh"

machineName="buildchroot"

machinectl terminate $machineName
systemd-machine-id-setup --root="$CHROOT_PATH"

systemd-nspawn --boot \
  --property='DeviceAllow=char-* rwm' \
  --property='DeviceAllow=block-* rwm' \
  --property='DeviceAllow=/dev/loop-control rwm' \
  --property='DeviceAllow=/dev/loop* rwm' \
  --capability=all --machine=$machineName --directory="$CHROOT_PATH" &
CONTAINER_PID=$!

sleep 20

until machinectl list | grep -q $machineName; do
    sleep 1
done

machinectl shell root@$machineName /build.sh
sleep 2
machinectl terminate $machineName
sleep 2
wait $CONTAINER_PID

/opt/syslbuild/deactive_chroot.sh "$CHROOT_PATH"

umount "$CHROOT_PATH/project"
