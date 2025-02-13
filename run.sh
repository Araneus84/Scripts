#!/bin/bash
if [ "$EUID" -ne 0 ]; then
   echo "This application requires root privileges"
   exec pkexec "$0" "$@"
fi
./bettercopyqt6
