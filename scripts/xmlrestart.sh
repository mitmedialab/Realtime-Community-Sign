#!/bin/sh
cd /opt/bin
if [ -e /var/run/lib-sign-ctrl-restart.pid ]
then
rm /var/run/lib-sign-ctrl-restart.pid
restart.sh
fi