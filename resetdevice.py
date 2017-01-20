#!/usr/bin/env python

# Workaround to fix problem where device has to be plugged out and in again to work
# https://github.com/elnerd/

import usb.core
import usb.util

import fcntl
import os

# Thanks to https://github.com/Paufurtado/usbreset.py
USBDEVFS_RESET = ord('U') << (4*2) | 20

def reset_usb_devicefile(filename):
        rc = fcntl.ioctl(open(filename,"w"), USBDEVFS_RESET, 0);

def reset_dongle():
        devs = usb.core.find(idVendor=0x1915, idProduct=0x0102, find_all=True)
        for dev in devs:
                bus = str(dev.bus).zfill(3)
                addr = str(dev.address).zfill(3)
                filename = "/dev/bus/usb/%s/%s" % (bus, addr)
                print "Resetting", filename
                reset_usb_devicefile(filename)
