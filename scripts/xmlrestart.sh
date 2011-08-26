#!/bin/sh
cd /opt/bin
if [ -e /var/run/lib-sign-ctrl.pid ]
then
rm /var/run/lib-sign-ctrl.pid
restart.sh
fi