Running an LED Sign on a Netgear WNR3500L Router
=======

1) Install TomatoUSB (via DD-WRT)
=======
We use a Netgear WNR3500L Router.  Unfortunately to install TomatoUSB on this router, we first need to install DD-WRT.  These instructions are taken from the DD-WRT website (<http://www.dd-wrt.com/wiki/index.php/Netgear_WNR3500L>).  They are included here for completeness.

**Versions**: For DD-WRT this router uses the NEWD-2, K2.6 build. _Do not use another version_ as this may brick the router.  For TomatoUSB this router uses K2.6 build for MIPSR2 (choose EXT or VPN).  Download both firmware builds to your PC first!

1. Use a static IP (ex 192.168.1.8) on the PC and connect the PC to the router using ethernet cable. You should not be flashing the router using a wireless network.
2. Do a hard reset (30/30/30) to clear the nvram - with the router on, hold the reset button for 30 seconds, unplug the power cord while still holding the reset button and hold it for 30 seconds, and plug the power cord back in while holding the reset button and hold it for 30 seconds. 
3. Go to http://192.168.1.1
4. Choose Router Upgrade from the menu and upload the .chk build (you need K2.6) of DD-WRT which can be found from the link above
5. After the site says that the upgrade has been completed, wait for awhile (at least 5 minutes).
6. Do another hard reset and clear the browser’s cache.
7. Repeat steps 3-6 using the TomatoUSB file (you can get the K2.6 MIPSR2 EXT or VPN file from <http://tomatousb.org/download>)

**User/passwords for Web GUIs**:
 
- For the original software by Netgear, the user/password combo is admin/password
- For DD-WRT, the default is root/admin
- For TomatoUSB, the default is admin/admin or root/root

2) Install Optware
========

The following steps require that yor router be connected to the internet and to your PC.  We tend to turn off wireless on our PC, connect it to the router over a wire, and set up the router as a wireless client on our existing wireless network (via the Basic > Network > Wireless options in the router web interface).  That allows our PC to access the router and both the router and PC to access the internet to download software we need.

Install Optware on a USB Key
--------
These instructions are taken from the TomatoUSB website (<http://tomatousb.org/tut:optware-installation>).  They are included here for completeness:

1. Log into your router with the web interface. Usually http://192.168.1.1
2. Go to USB and NAS > USB Support and enable all the USB options
3. Format your USB key (at least 512MB) - we found this easiest to do on an Ubuntu PC, formatting it as ext2 and labeling the one partition _optware_
4. Plug the usb drive into your router and you should see it show up on at the bottom of the USB Support page from step #2
5. In the router's web interface go to Administration > Scripts > Init and add the following line so that Tomato mounts the drive automatically in the right place (/opt):
    `echo "LABEL=optware /opt ext2 defaults 1 1" >> /etc/fstab`
6. Reboot your router
7. Check the USB and NAS > USB Support webpage again and you should see a note that your USB devices is mounted to /opt
8. SSH to your router: `ssh root@192.168.1.1`
9. Run the following code to get optware installed on the USB key (this will take a minute):
    - `wget http://tomatousb.org/local--files/tut:optware-installation/optware-install.sh -O - | tr -d '\r' > /tmp/optware-install.sh`
	- `chmod +x /tmp/optware-install.sh`
	- `sh /tmp/optware-install.sh`
10. Run the following commands to install required libraries:
```
ipkg install python26
ipkg install py26-serial
ipkg install py26-setuptools
ipkg install git
```

2) Configure TomatoUSB
========

Get Our Software
--------

1. SSH to your router: `ssh root@192.168.1.1`
2. a) Get our code from Github via https (easy):
 ```
cd /opt/usr/lib/
git init
git clone https://YOUR_USERNAME@github.com/c4fcm/Realtime-Community-Sign.git
 ```
2. b) Get our code from Github via keys (annoying):
```
dropbearkey -t rsa -f id_rsa
mv id_rsa /opt/usr/lib/id_rsa
mv /opt/usr/lib/Realtime-Community-Sign/scripts/sshlib /opt/bin
export GIT_SSH =/opt/bin/sshlib
```
(this export command has to be run every time you want to access the server, to commit or pull for example)
3. Move some scripts to better places:
```
mv /opt/usr/lib/Realtime-Community-Sign/scripts/restart.sh /opt/bin
mv /opt/usr/lib/Realtime-Community-Sign/scripts/xmlrestart.sh /opt/bin
```

Configure TomatoUSB to Run Our Software
--------

**Set up some Schedules on the Administration > Scheduler**

1. enable Reboot - set to 1:00 AM, Everyday
2. enable Custom 1 - set to Every hour, Everyday
	cd /opt/bin
	./restart.sh
3. enable Custom 2 - set to Every minute, Everyday
	cd /opt/bin
	./xmlrestart.sh

**Set Up Our Scripts in Administration -> Scripts**

1. under Init (for kernel modules to support usb-serial installation)
	insmod usbserial
	insmod ftdi_sio
	insmod pl2303
2. under Firewall
	cd /opt/usr/lib/Realtime-Community-Sign/	python2.6 lib-sign-ctrl.py

Reboot router after these changes have been done.
