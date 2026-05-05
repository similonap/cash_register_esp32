#!/usr/bin/env bash
# deploy.sh — copy nfc_reader_demo to the connected ESP32 and run main.py
#
# Requires: mpremote  (pip install mpremote)
# Usage:    ./deploy.sh [port]
#   port defaults to auto-detect (first /dev/cu.usbserial-* or /dev/ttyUSB*)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HANNA_DIR="$(cd "$SCRIPT_DIR/../hanna_light" && pwd)"

PORT="${1:-}"
if [ -z "$PORT" ]; then
  PORT="$(ls /dev/cu.usbserial-* /dev/cu.SLAB_USBtoUART /dev/ttyUSB* 2>/dev/null | head -1 || true)"
fi

if [ -z "$PORT" ]; then
  echo "ERROR: No ESP32 serial port found. Plug in the device or pass the port as an argument."
  echo "  Usage: $0 /dev/cu.usbserial-XXXX"
  exit 1
fi

echo ">>> Using port: $PORT"

echo ">>> Copying project files ..."
for f in main.py mfrc522.py config.py wifi.py; do
  echo "    $f"
  mpremote connect "$PORT" cp "$SCRIPT_DIR/$f" ":$f"
done

echo ">>> Copying LCD library from hanna_light ..."
for f in I2C_LCD.py LCD_API.py; do
  echo "    $f"
  mpremote connect "$PORT" cp "$HANNA_DIR/$f" ":$f"
done

echo ">>> Running main.py ..."
mpremote connect "$PORT" run "$SCRIPT_DIR/main.py"
