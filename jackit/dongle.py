#!/usr/bin/env python3
""" file to hold class for dongle management """

import os.path
import subprocess
from enum import Enum
from typing import Union

import array
import logging
import sys
import time
# this requirement is fulfilled by pyusb
# noinspection PyPackageRequirements
import usb

try:
    from fcntl import ioctl
except ImportError:
    # Make sure this code does not break platforms without ioctl - if any...
    ioctl = lambda *args: None


class Dongle(object):
    """ class for dongle management """
    dongle_device: Union[usb.core.Device, None]
    usb_timeout: int
    in_bootloader: bool

    usb_timeout = 2500

    def __init__(self, dongle_specifier):
        self.dongle_specifier = dongle_specifier
        dongle_list: list[usb.core.Device] = self.list()
        logging.debug("got list of dongles")
        logging.debug(dongle_list)
        self.dongle_device = None
        self.usb_timeout = Dongle.usb_timeout

        if len(dongle_list) == 0:
            logging.warning("did not find any dongles")
            return
        if dongle_specifier is None:
            self.dongle_device = dongle_list[0]
            logging.info("choosing first dongle at address: " + str(self.dongle_device.address))
        else:
            logging.info("dongle specifier is: " + self.dongle_specifier)
            for dongle in dongle_list:
                if str(dongle.address) == dongle_specifier:
                    self.dongle_device = dongle
                    logging.info("choosing dongle at address " + str(self.dongle_device.address))
        self.dongle_device.set_configuration()  # start the dongle
        return

    @staticmethod
    def build_firmware():
        """
        builds the firmware if required
        """
        print("looks like we need to build the firmware")
        print("make sure you have installed SDCC and GNU Binutils")

        # from: https://github.com/BastilleResearch/mousejack/issues/33
        objcopy_path = "objcopy"
        # special case for Apple Silicon
        if os.path.exists(
                "/opt/homebrew/opt/binutils/bin/objcopy"):
            objcopy_path = "/opt/homebrew/opt/binutils/bin/objcopy"
            logging.info("using objcopy from the homebrew path")

        build_dir = os.path.dirname(os.path.realpath(__file__)) + "/lib/"
        # noinspection SpellCheckingInspection
        build_script = """
        sdcc --model-large --std-sdcc99 -c src/main.c -o bin/main.rel
        sdcc --model-large --std-sdcc99 -c src/usb.c -o bin/usb.rel
        sdcc --model-large --std-sdcc99 -c src/usb_desc.c -o bin/usb_desc.rel
        sdcc --model-large --std-sdcc99 -c src/radio.c -o bin/radio.rel
        sdcc --/ram-loc 0x8000 --xram-size 2048 --model-large bin/main.rel bin/usb.rel bin/usb_desc.rel bin/radio.rel -o bin/dongle.ihx
        objcopy -I ihex bin/dongle.ihx -O binary bin/dongle.bin
        objcopy --pad-to 26622 --gap-fill 255 -I ihex bin/dongle.ihx -O binary bin/dongle.formatted.bin
        objcopy -I binary bin/dongle.formatted.bin -O ihex bin/dongle.formatted.ihx
        """
        build_script = build_script.replace("objcopy", objcopy_path)
        for line in build_script.splitlines():
            logging.info(subprocess.run(line, shell=True, capture_output=True, cwd=build_dir))

    def jump_dongle_to_bootloader(self):
        """
        jumps the dongle to bootloader
        """
        logging.info("Looking for a compatible device that can jump to the Nordic bootloader")
        # note: it is possible to have a device by this vendor present that is not a compatible dongle
        self.dongle_device = usb.core.find(idVendor=0x1915)

        if self.dongle_device is None:
            logging.info(
                "could not find a device that can jump to bootloader, checking for devices that are in bootloader")
            self.dongle_device = Dongle.get_in_bootloader()
            if self.dongle_device is usb.core.Device:
                logging.info("found a device that is in bootloader, skipping this step")
                return
            else:
                logging.error("could not find a device that is in bootloader, check your devices")
                sys.exit(1)

        self.dongle_device.reset()
        self.dongle_device.set_configuration()
        if self.dongle_device.product == 0x0102:
            self.dongle_device.write(0x01, [0xFF], timeout=self.usb_timeout)
        else:
            # noinspection PyArgumentEqualDefault
            self.dongle_device.ctrl_transfer(0x40, 0xFF, 0, 0, (), timeout=self.usb_timeout)

        self.dongle_device.reset()
        logging.info("waiting for dongle to get to bootloader")
        time.sleep(1)

    def start_flash(self):
        """
        Build and flash the firmware.
        """

        if len(Dongle.list()) != 0:
            logging.error("a connected dongle already has the NRF firmware")
            sys.exit(1)

        self.dongle_device = self.get_in_bootloader()  # get the device that is in the bootloader
        if isinstance(self.dongle_device, usb.core.Device):
            # we do the flash here
            # adapted from https://github.com/BastilleResearch/nrf-research-firmware/blob/master/prog/usb-flasher/usb-flash.py
            logging.info("checking to see if we need to build firmware")

            firmware_path = os.path.dirname(os.path.realpath(__file__)) + "/lib/bin/dongle.bin"
            if not os.path.exists(firmware_path):
                Dongle.build_firmware()

            logging.info("firmware present")

            # Read in the firmware
            logging.info("reading firmware file")
            with open(firmware_path, 'rb') as firmware_file:
                firmware_data = firmware_file.read()

            # Zero pad the data to a multiple of 512 bytes
            firmware_data += b'\000' * (512 - len(firmware_data) % 512)

            logging.info("found firmware of size: " + str(len(firmware_data)))

            logging.info("proceeding to flash dongle")
            # Write the data, one page at a time
            logging.info("Writing image to flash")
            page_count = len(firmware_data) // 512

            self.dongle_device.set_configuration()
            for page in range(page_count):
                # Tell the bootloader that we are going to write a page
                self.dongle_device.write(0x01, [0x02, page])
                self.dongle_device.read(0x81, 64, self.usb_timeout)

                # Write the page as 8 pages of 64 bytes
                for block in range(8):
                    # Write the block
                    block_write = firmware_data[page * 512 + block * 64:page * 512 + block * 64 + 64]
                    self.dongle_device.write(0x01, block_write, self.usb_timeout)
                    self.dongle_device.read(0x81, 64, self.usb_timeout)

            # Verify that the image was written correctly, reading one page at a time
            logging.info("Verifying write")
            block_number = 0
            for page in range(page_count):
                # Tell the bootloader that we are reading from the lower 16KB of flash
                self.dongle_device.write(0x01, [0x06, 0], self.usb_timeout)
                self.dongle_device.read(0x81, 64, self.usb_timeout)

                # Read the page as 8 pages of 64 bytes
                for block in range(8):
                    # Read the block
                    self.dongle_device.write(0x01, [0x03, block_number], self.usb_timeout)
                    block_read = self.dongle_device.read(0x81, 64, self.usb_timeout)
                    if block_read != array.array('B', firmware_data[block_number * 64:block_number * 64 + 64]):
                        raise Exception('Verification failed on page {0}, block {1}'.format(page, block))
                    block_number += 1

            logging.info("Firmware programming completed successfully")
            logging.info("\033[92m\033[1mPlease unplug your dongle or breakout board and plug it back in.\033[0m")

        elif self.dongle_device is None:  # if the current device is not yet in bootloader
            self.jump_dongle_to_bootloader()
            self.start_flash()  # retry this function in hopes that dongle is in bootloader
        else:
            logging.error(str(type(self.dongle_device)))
            raise Exception("Confused... strange combination, this should never happen.")

    @staticmethod
    def get_not_flashed() -> Union[usb.core.Device, None]:
        """
        gets the dongle that is running the CrazyRadio or RFStorm firmware
        """
        # Find an attached device running CrazyRadio or RFStorm firmware
        logging.info("Looking for a compatible device that can jump to the Nordic bootloader.")
        product_ids = [0x0102, 0x7777]
        for product_id in product_ids:
            # Find a compatible device
            dongle = usb.core.find(idVendor=0x1915, idProduct=product_id)
            logging.info("Found a device with the product id " + str(product_id) + ", continuing.")
            return dongle
        return None

    @staticmethod
    def list() -> [usb.core.Device]:
        """
        returns a list of the dongles that have the NRF firmware flashed
        """
        found = []
        for dongle in usb.core.find(idVendor=0x1915, idProduct=0x0102, find_all=True):
            found.append(dongle)
        return found

    @staticmethod
    def get_in_bootloader() -> Union[usb.core.Device, None]:
        """
        returns a list of dongles that are in bootloader
        """
        logging.info("looking for dongles that are in bootloader")
        wait_time = 1
        logging.info("Waiting " + str(wait_time) + " seconds to find dongles.")
        end_time = time.time() + wait_time
        device = None
        while device is None and end_time > time.time():
            device = usb.core.find(idVendor=0x1915, idProduct=0x0101)
        return device

    def reset(self):
        """
        reset the dongle's usb device
        """
        # Thanks to https://github.com/Paufurtado/usbreset.py
        # noinspection PyPep8Naming,SpellCheckingInspection
        USBDEVFS_RESET = ord('U') << (4 * 2) | 20
        bus = str(self.dongle_device.bus).zfill(3)
        addr = str(self.dongle_device.address).zfill(3)
        filename = "/dev/bus/usb/%s/%s" % (bus, addr)
        try:
            ioctl(open(filename, "w"), USBDEVFS_RESET, 0)
        except IOError:
            print("Unable to reset device %s" % filename)

    # USB commands
    class USBCommand(Enum):
        """
        Enum for usb commands to dongles
        """
        TRANSMIT_PAYLOAD = 0x04
        ENTER_SNIFFER_MODE = 0x05
        ENTER_PROMISCUOUS_MODE = 0x06
        ENTER_TONE_TEST_MODE = 0x07
        TRANSMIT_ACK_PAYLOAD = 0x08
        SET_CHANNEL = 0x09
        GET_CHANNEL = 0x0A
        ENABLE_LNA_PA = 0x0B
        TRANSMIT_PAYLOAD_GENERIC = 0x0C
        ENTER_PROMISCUOUS_MODE_GENERIC = 0x0D
        RECEIVE_PAYLOAD = 0x12

    # nRF24LU1+ registers
    RF_CH = 0x05

    # RF data rates
    RF_RATE_250K = 0
    RF_RATE_1M = 1
    RF_RATE_2M = 2

    # nRF24LU1+ radio dongle

    def enter_promiscuous_mode(self, prefix=None):
        """
        put the radio in pseudo-promiscuous mode
        """
        if prefix is None:
            prefix = []
        self.send_usb_command(self.USBCommand.ENTER_PROMISCUOUS_MODE.value, [len(prefix)] + prefix)
        self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)
        if len(prefix) > 0:
            logging.debug('Entered promiscuous mode with address prefix {0}'.format(
                ':'.join('{:02X}'.format(b) for b in prefix)))
        else:
            logging.debug('Entered promiscuous mode')

    def enter_promiscuous_mode_generic(self, prefix=None, rate=RF_RATE_2M):
        """
        Put the radio in pseudo-promiscuous mode without CRC checking
        """
        if prefix is None:
            prefix = []
        self.send_usb_command(self.USBCommand.ENTER_PROMISCUOUS_MODE_GENERIC.value, [len(prefix), rate] + prefix)
        self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)
        if len(prefix) > 0:
            logging.debug('Entered generic promiscuous mode with address prefix {0}'.format(
                ':'.join('{:02X}'.format(b) for b in prefix)))
        else:
            logging.debug('Entered promiscuous mode')

    def enter_sniffer_mode(self, address):
        # noinspection SpellCheckingInspection
        """
        Put the radio in ESB "sniffer" mode (ESB mode w/o auto-acking)
        """
        self.send_usb_command(self.USBCommand.ENTER_SNIFFER_MODE.value, [len(address)] + address)
        self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)
        logging.debug(
            'Entered sniffer mode with address {0}'.format(':'.join('{:02X}'.format(b) for b in address[::-1])))

    def enter_tone_test_mode(self):
        """
        Put the radio into continuous tone (TX) test mode
        """
        self.send_usb_command(self.USBCommand.ENTER_TONE_TEST_MODE.value, [])
        self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)
        logging.debug('Entered continuous tone test mode')

    def receive_payload(self):
        """
        Receive a payload if one is available
        """
        self.send_usb_command(self.USBCommand.RECEIVE_PAYLOAD.value, ())
        try:
            payload = self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)
        except usb.core.USBError:
            logging.error("Could not read from dongle, It looks like the dongle may have been unplugged.")
            sys.exit(1)
        return payload

    def transmit_payload_generic(self, payload, address=None):
        """
        Transmit a generic (non-ESB) payload
        """
        if address is None:
            address = [0x33, 0x33, 0x33, 0x33, 0x33]
        data = [len(payload), len(address)] + payload + address
        self.send_usb_command(self.USBCommand.TRANSMIT_PAYLOAD_GENERIC.value, data)
        return self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)[0] > 0

    def transmit_payload(self, payload, timeout=4, retransmits=15):
        """
        Transmit an ESB payload
        """
        data = [len(payload), timeout, retransmits] + payload
        self.send_usb_command(self.USBCommand.TRANSMIT_PAYLOAD.value, data)
        return self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)[0] > 0

    def transmit_ack_payload(self, payload):
        """
        Transmit an ESB ACK payload
        """
        data = [len(payload)] + payload
        self.send_usb_command(self.USBCommand.TRANSMIT_ACK_PAYLOAD.value, data)
        return self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)[0] > 0

    def set_channel(self, channel):
        """
        Set the RF channel
        """
        if channel > 125:
            channel = 125
        self.send_usb_command(self.USBCommand.SET_CHANNEL.value, [channel])
        self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)
        logging.debug('Tuned to {0}'.format(channel))

    def get_channel(self):
        """
        Get the current RF channel
        """
        self.send_usb_command(self.USBCommand.GET_CHANNEL.value, [])
        return self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)

    def enable_lna(self):
        """
        Enable the LNA (CrazyRadio PA)
        """
        self.send_usb_command(self.USBCommand.ENABLE_LNA_PA.value, [])
        self.dongle_device.read(0x81, 64, timeout=self.usb_timeout)

    def send_usb_command(self, request, data):
        """
        Send a USB command
        """
        data = [request] + list(data)
        try:
            self.dongle_device.write(0x01, data, timeout=self.usb_timeout)
        except AttributeError:
            logging.error("Could not write to dongle, please ensure that one is connected with the correct firmware.")
            sys.exit(1)
