#!/usr/bin/env python3
""" file to hold class for dongle management """

import logging
import time
from typing import Union, Any, Generator

# noinspection PyPackageRequirements (this requirement is satisfied by pyusb)
import usb


class Dongle(object):
    """ class for dongle management """

    def __init__(self):
        return

    @staticmethod
    def list():
        """
        return a list of dongles
        """
        found = []
        # Find an attached device running CrazyRadio or RFStorm firmware
        logging.info("Looking for a compatible device that can jump to the Nordic bootloader.")
        product_ids = [0x0102, 0x7777]
        for product_id in product_ids:
            # Find a compatible device
            try:
                dongle: usb.core.Device = usb.core.find(idVendor=0x1915, idProduct=product_id)
                logging.info("Found a device with the product id " + str(product_id) + ", continuing.")
                dongle.set_configuration()
                found.append(dongle)
            except AttributeError:
                logging.info("Could not find a device with the product id " + str(product_id) + ", continuing.")
                continue

        logging.info("Looking for a device running the Nordic bootloader.")

        wait_time = 2
        logging.info("Waiting " + str(wait_time) + " seconds to find dongles.")
        end_time = time.time() + 5
        while time.time() < end_time:
            # Find devices running the Nordic bootloader
            try:
                dongle = usb.core.find(idVendor=0x1915, idProduct=0x0101)
                dongle.set_configuration()
                found.append(dongle)
                break
            except AttributeError:
                continue

        return found
