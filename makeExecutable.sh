#!/bin/bash

# Check if the platform argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 {linux|win|mac}"
  exit 1
fi

PLATFORM=$1

case $PLATFORM in
  linux)
    pyinstaller stag_gui_linux.spec
    ;;
  win)
    pyinstaller stag_gui.py --collect-all ram --onefile --windowed --add-data images:images
    ;;
  mac)
    pyinstaller stag_gui.py --collect-all ram --add-data images:images --onedir --windowed
    ;;
  *)
    echo "Invalid platform. Please specify 'linux', 'win', or 'mac'."
    exit 1
    ;;
esac

echo "Build process completed for platform: $PLATFORM"
