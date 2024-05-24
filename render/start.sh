#!/bin/sh
# Run dummy monitor
rm -f /tmp/.X1-lock
/usr/bin/Xorg -noreset +extension GLX +extension RANDR +extension RENDER -logfile ./xdummy.log -config /etc/X11/xorg.conf :1 & 
# Start Uvicorn App
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug --workers 16
