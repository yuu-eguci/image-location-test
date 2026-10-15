#!/bin/sh
# 仮想ディスプレイで ImageTest を起動し、noVNC (http://localhost:6080/vnc.html) で見られるようにする。
set -e
# 止めたコンテナをもう一度起動したときに、前回の Xvfb のロックが残っていると起動できないので消す
rm -f /tmp/.X0-lock /tmp/.X11-unix/X0
Xvfb :0 -screen 0 640x480x24 -nolisten tcp &
# Xvfb の準備ができるまで待つ (10 秒で諦める)
for _ in $(seq 100); do [ -e /tmp/.X11-unix/X0 ] && break; sleep 0.1; done
[ -e /tmp/.X11-unix/X0 ] || { echo 'Xvfb が起動しませんでした' >&2; exit 1; }
export DISPLAY=:0
x11vnc -display :0 -localhost -rfbport 5900 -forever -shared -nopw -quiet &
websockify --web /opt/novnc 6080 localhost:5900 >/dev/null 2>&1 &
# ImageTest を終了 (ESC) したらコンテナも止まる
exec python /app/ImageTest.py
