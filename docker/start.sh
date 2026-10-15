#!/bin/sh
# 仮想ディスプレイで ImageTest を起動し、noVNC (http://localhost:6080/vnc.html) で見られるようにする。
set -e
Xvfb :0 -screen 0 640x480x24 -nolisten tcp &
until [ -e /tmp/.X11-unix/X0 ]; do sleep 0.1; done
export DISPLAY=:0
x11vnc -display :0 -localhost -rfbport 5900 -forever -shared -nopw -quiet &
websockify --web /opt/novnc 6080 localhost:5900 >/dev/null 2>&1 &
# ImageTest を終了 (ESC) したらコンテナも止まる
exec python /app/ImageTest.py
