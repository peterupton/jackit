#!/usr/bin/env python3
"""
file to hold class for attack management
"""
import logging
import time

import dongle


class Attack(object):
    """class for attack management"""

    def __init__(self, current_dongle: dongle.Dongle, enable_lna):
        self.current_dongle = current_dongle
        self.init_radio(enable_lna)
        self.channels = range(2, 84)
        self.channel_index = 0

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

    def scan(self, callback, dwell_time: float = 0.1):
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
                #logging.info("ch: %02d addr: %s packet: %s" % (self.channels[self.channel_index], self.to_display(address), self.to_display(payload)))
                if callback(self.channel_index, address, payload):  # if we got True from the callback function, then we need to stop
                    return self.channel_index, address, payload

    def sniff(self, address, callback=None):
        if address is None:
            self.scan()
        self.radio.enter_sniffer_mode(address)
        self.channel_index = 0
        self.radio.set_channel(self.channels[self.channel_index])
        dwell_time = 0.1
        last_ping = time.time()
        start_time = time.time()

        while time.time() - start_time < timeout:
            if len(self.channels) > 1 and time.time() - last_ping > dwell_time:
                if not self.radio.transmit_payload(self.ping, 1, 1):
                    success = False
                    for self.channel_index in range(len(self.channels)):
                        self.radio.set_channel(self.channels[self.channel_index])
                        if self.radio.transmit_payload(self.ping, 1, 1):
                            last_ping = time.time()
                            success = True
                            self._debug("Ping success on channel %d" % self.channels[self.channel_index])
                            break

                    if not success:
                        self._debug("Ping failed")
                else:
                    last_ping = time.time()

            try:
                value = self.radio.receive_payload()
            except RuntimeError:
                value = [1]

            if value[0] == 0:
                # hack to keep it on channel
                last_ping = time.time() + 5.0
                payload = value[1:]
                self._debug("ch: %02d addr: %s packet: %s" % (self.channels[self.channel_index], addr_string, self.to_display(payload)))
                if callback:
                    callback(address, payload)
                else:
                    self.add_device(addr_string, payload)

        return self.devices

