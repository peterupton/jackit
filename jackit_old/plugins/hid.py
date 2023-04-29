"""
this file contains the parent class for all "HID" decoder/encoder classes
"""
import abc
from abc import ABCMeta


class HID(metaclass=ABCMeta):
    """abstract class for HIDs"""

    @abc.abstractmethod
    def __init__(self, address, payload):
        self.address = address
        self.device_vendor = None
        self.payload_template = [0, 0xC1, 0, 0, 0, 0, 0, 0, 0, 0]
        self.keepalive = [0x00, 0x40, 0x04, 0xB0, 0x0C]
        self.hello = [0x00, 0x4F, 0x00, 0x04, 0xB0, 0x10, 0x00, 0x00, 0x00, 0xED]
        self.description = None

    @abc.abstractmethod
    def key(self, payload, key):
        """? set payload for desired key"""
        """
        payload[19:24] = [0, 0, 0, 0, 0]
        payload[20] = key['mod']
        payload[22] = key['hid']
        return payload
        """
        pass

    @abc.abstractmethod
    def frame(self, key=None):
        """? build frame from payload template, key and optionally checksum if needed"""
        """
        if key is None:
            key = {'hid': 0, 'mod': 0}
        """
        pass

    @abc.abstractmethod
    def build_frames(self, attack):
        """
        ?build frames for attack
        """
        """
        for i in range(0, len(attack)):
            key = attack[i]

            if i == 0:
                key['frames'] = [[self.hello[:], 12]]
            else:
                key['frames'] = []

            if i < len(attack) - 1:
                next_key = attack[i + 1]
            else:
                next_key = None

            if key['hid'] or key['mod']:
                key['frames'].append([self.frame(key), 12])
                key['frames'].append([self.keepalive[:], 0])
                if not next_key or key['hid'] == next_key['hid'] or next_key['sleep']:
                    key['frames'].append([self.frame(), 0])
            elif key['sleep']:
                count = int(key['sleep']) / 10
                for i in range(0, int(count)):
                    key['frames'].append([self.keepalive[:], 10])
        """

    @classmethod
    def fingerprint(cls, payload):
        """
        fingerprint a device from a payload
        """
        pass

    @classmethod
    def description(cls):
        """
        returns the description of this HID class
        """
        return cls.description
