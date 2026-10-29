#!/bin/bash
set -e

DEV_TOOLS="/mnt/ldata/development/support/winre_tools"
EMBED_PYTHON="/mnt/ldata/development/support/winre_tools/python-3.14.8-embed-amd64/"

# 1. Set usb location
USB_LOCATION=/run/media/don/6F09-A924/


# 2. Clean and sync Python embeddable distribution
sudo rm -rf "$USB_LOCATION/Python"
sudo mkdir -p "$USB_LOCATION/Python"
sudo cp -r "$EMBED_PYTHON"/* "$USB_LOCATION/Python/"

# 3. Copy recovery scripts and tools
sudo mkdir -p "$USB_LOCATION/tools"
sudo cp -r "$DEV_TOOLS"/* "$USB_LOCATION/tools/"

# 4. Copy launcher batch script to drive root (handles both .cmd and .bat)
if [ -f "$DEV_TOOLS/run_diag.cmd" ]; then
    sudo cp "$DEV_TOOLS/run_diag.cmd" "$USB_LOCATION/run_diag.cmd"
elif [ -f "$DEV_TOOLS/run_diag.bat" ]; then
    sudo cp "$DEV_TOOLS/run_diag.bat" "$USB_LOCATION/run_diag.bat"
fi


echo "[+] Copied tools to USB successfully!"
