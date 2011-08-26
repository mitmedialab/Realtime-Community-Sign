#!/bin/sh
cd /opt/usr/lib/lib-display-code/router-led
prid=$(pidof python2.6 lib-sign-ctrl.py)
kill -9 $prid
sleep 5
python2.6 lib-sign-ctrl.py
