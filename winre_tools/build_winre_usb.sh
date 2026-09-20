#!/bin/bash
set -e

MOUNT_DIR="/tmp/usb_mnt"
IMG_PATH="/mnt/ldata/winre-env/winre_usb.img"
DEV_TOOLS="/mnt/ldata/development/support/winre_tools"
EMBED_PYTHON="/mnt/ldata/winre-env/python-3.13.15-embed-amd64"

# 1. Ensure mount point exists and mount image
mkdir -p "$MOUNT_DIR"
sudo mount -o loop "$IMG_PATH" "$MOUNT_DIR"

# 2. Clean and sync Python embeddable distribution
sudo rm -rf "$MOUNT_DIR/Python"
sudo mkdir -p "$MOUNT_DIR/Python"
sudo cp -r "$EMBED_PYTHON"/* "$MOUNT_DIR/Python/"

# 3. Copy recovery scripts and tools
sudo mkdir -p "$MOUNT_DIR/tools"
sudo cp -r "$DEV_TOOLS"/* "$MOUNT_DIR/tools/"

# 4. Copy launcher batch script to drive root (handles both .cmd and .bat)
if [ -f "$DEV_TOOLS/run_diag.cmd" ]; then
    sudo cp "$DEV_TOOLS/run_diag.cmd" "$MOUNT_DIR/run_diag.cmd"
elif [ -f "$DEV_TOOLS/run_diag.bat" ]; then
    sudo cp "$DEV_TOOLS/run_diag.bat" "$MOUNT_DIR/run_diag.bat"
fi

# 5. Flush writes to disk image and unmount cleanly
sudo sync
sudo umount "$MOUNT_DIR"

echo "[+] Virtual USB image built successfully!"