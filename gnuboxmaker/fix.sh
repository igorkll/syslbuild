#!/bin/bash
set -e

# ----------------------------------- allow start pipewire from root

UNITS=(
    "pipewire.service"
    "pipewire.socket"
    "pipewire-pulse.service"
    "pipewire-pulse.socket"
    "wireplumber.service"
)

OVERRIDE_DIR="/root/.config/systemd/user"

mkdir -p "$OVERRIDE_DIR"

for unit in "${UNITS[@]}"; do
    unit_override_dir="$OVERRIDE_DIR/${unit}.d"
    mkdir -p "$unit_override_dir"

    cat > "$unit_override_dir/override.conf" <<EOF
[Unit]
ConditionUser=
EOF
done
